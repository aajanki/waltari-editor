import React from 'react';
import ReactQuill, { Quill, UnprivilegedEditor } from 'react-quill';
import { DeltaStatic, DeltaOperation } from 'quill';
import 'react-quill/dist/quill.snow.css';

let Inline = Quill.import('blots/inline');
let Delta = Quill.import('delta')

class PassiveBlot extends Inline {}
PassiveBlot.blotName = 'passive';
PassiveBlot.tagName = 'mark';
PassiveBlot.className = 'annotation-passive';

class AdverbBlot extends Inline {}
AdverbBlot.blotName = 'adverb';
AdverbBlot.tagName = 'mark';
AdverbBlot.className = 'annotation-adverb';

class DifficultBlot extends Inline {}
DifficultBlot.blotName = 'difficult';
DifficultBlot.tagName = 'mark';
DifficultBlot.className = 'annotation-difficult';

Quill.register({
    'formats/adverb': AdverbBlot,
    'formats/passive': PassiveBlot,
    'formats/difficult': DifficultBlot,
});

const annotationTypes = ['passive', 'adverb', 'difficult'];

type SpanAnnotation = {
    start: number;
    length: number;
    label: string;
}

interface AnnotatingEditorProps {
    onCountsChange: (
        words: number,
        sentences: number,
        adverbs: number,
        passives: number,
        readability: number,
        readability2: number,
    ) => void
}

function cancellableTimeout<T>(ms: number, value: T, options: { signal?: AbortSignal; } = {}) : Promise<T> {
    return new Promise((resolve, reject) => {
        const listener = () => {
            clearTimeout(timer);
            reject(options.signal?.reason);
        };
        options.signal?.throwIfAborted();
        const timer = setTimeout(() => {
            options.signal?.removeEventListener('abort', listener);
            resolve(value);
        }, ms);
        options.signal?.addEventListener('abort', listener);
    });
}

/**
 * A Promise that is either completed after the specified amount of time or aborted.
 * @param ms Delay in milliseconds
 * @param abortSignal AbortSignal object that can be used to cancel the wait.
 * @returns True, if waited for the specified time. False if the wait got cancelled before completion.
 */
async function wait(ms: number, abortSignal: AbortSignal): Promise<boolean> {
    try {
        await cancellableTimeout(ms, null, { signal: abortSignal });
    } catch (e) {
        if (e instanceof DOMException) {
            // the wait was cancelled
            return false;
        } else {
            throw e;
        }
    }

    return true;
}

export class AnnotatingEditor extends React.Component<AnnotatingEditorProps> {

    generation: number;

    abortController: AbortController | undefined;

    editorRef: React.RefObject<ReactQuill>;

    constructor(props: AnnotatingEditorProps) {
        super(props);

        this.generation = 0;
        this.editorRef = React.createRef();
    }

    fetchAnnotations = async (text: string) => {
        const requestBody = {
            text: text
        };
        const rawResponse = await fetch('/api/annotate', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!rawResponse.ok) {
            throw new Error(`Annotation request failed: ${rawResponse.status}`);
        }

        return await rawResponse.json();
    }

    onChangeHandler = async (content: string, delta: DeltaStatic, source: string, editor: UnprivilegedEditor) : Promise<void> => {
        if (source !== 'user') {
            return;
        }

        if (typeof this.abortController === 'object') {
            // There were additional edits during the waiting period. Cancel
            // the earlier timer to signal that it's not necessary to call the
            // API for the previous change because they got obsoleted by this
            // latest change.
            this.abortController.abort();
            this.abortController = undefined;
        }

        this.generation += 1;
        const currentGeneration = this.generation;
        const text = editor.getText();

        // Wait for more edits for 300 milliseconds before calling the API.
        this.abortController = new AbortController();
        const waitCompleted = await wait(300, this.abortController.signal);

        if (!waitCompleted) {
            // Additional changes were made during the wait period. Discard 
            // this generation.
            return;
        }

        this.abortController = undefined;

        return await this.annotate(text, currentGeneration);
    }

    annotate = async (text: string, currentGeneration: number) : Promise<void> => {
        const response = await this.fetchAnnotations(text);

        // Update the annotations only, if the text hasn't changed since we called
        // the annotation API
        if (currentGeneration === this.generation) {
            this.updateAnnotations(response.annotations, text.length);

            this.props.onCountsChange(
                response.count_words,
                response.count_sentences,
                response.count_adverb_words,
                response.count_passive_sentences,
                response.readability,
                response.readability_long_words,
            );
        }
    }

    updateAnnotations = (annotations: SpanAnnotation[], textLength: number) : void => {
        let i = 0;
        let ops: DeltaOperation[] = [];
        const deleteAttributes = Object.fromEntries(annotationTypes.map(x => [x, null]));

        // Convert annotations API response to a Delta object
        annotations.sort(this.annotationSortValue);
        for (const annotation of annotations) {
            let start = annotation.start;
            let length = annotation.length;

            if (start < i) {
                // Skip overlapping annotations
                continue;
            } else if (start > i) {
                // Remove obsolete annotations
                ops.push({retain: start - i, attributes: deleteAttributes});
            }

            // Add the new annotation
            ops.push({retain: length, attributes: {[annotation.label]: true}});

            i = start + length;
        }

        // Remove existing annotations in the remaining text after the last span
        const lastAnnotationPos = annotations.length === 0
            ? 0
            : annotations[annotations.length - 1].start + annotations[annotations.length - 1].length;
        const remainingCharCount = textLength - lastAnnotationPos;
        if (remainingCharCount > 0) {
            ops.push({retain: remainingCharCount, attributes: deleteAttributes});
        }

        const delta = new Delta(ops);
        const editor = this.editorRef.current;
        if (editor !== null) {
            editor.getEditor().updateContents(delta, 'api');
        }
    }

    annotationSortValue(a: SpanAnnotation, b: SpanAnnotation): number {
        const position_diff = a.start - b.start;

        if (position_diff === 0) {
            if (a.label === "difficult" && a.label !== "difficult") {
                return -1;
            } else if (a.label !== "difficult" && a.label === "difficult") {
                return 1;
            }
        }

        return position_diff;
    }

    render() {
        const modules = {
            toolbar: [
                ['bold', 'italic', 'underline'],
                [{'list': 'ordered'}, {'list': 'bullet'}]
            ]
        };
        const formats = [
            'bold', 'font', 'italic', 'link', 'size', 'underline', 'indent',
            'list', 'direction'
        ].concat(annotationTypes);

        return <ReactQuill
            theme='snow'
            modules={modules}
            formats={formats}
            onChange={this.onChangeHandler}
            ref={this.editorRef}
        />;
      }

      componentWillUnmount(): void {
        if (typeof this.abortController === 'object') {
            this.abortController.abort();
            this.abortController = undefined;
        }
      }
};
