import React from 'react';
import ReactQuill, { Quill, UnprivilegedEditor } from 'react-quill';
import { DeltaStatic, DeltaOperation } from 'quill';
import './quill.snow.larger.css';

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

Quill.register({
    'formats/adverb': AdverbBlot,
    'formats/passive': PassiveBlot,
});

type SpanAnnotation = {
    start: number;
    length: number;
    label: string;
}

interface AnnotatingEditorProps {
    onCountsChange: (words: number, sentences: number, adverbs: number, passives: number) => void
}

export class AnnotatingEditor extends React.Component<AnnotatingEditorProps> {

    generation: number;

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
        return await rawResponse.json();
    }

    onChangeHandler = async (content: string, delta: DeltaStatic, source: string, editor: UnprivilegedEditor) => {
        if (source !== 'user') {
            return;
        }

        this.generation += 1;
        const currentGeneration = this.generation;

        const response = await this.fetchAnnotations(editor.getText());

        if (currentGeneration === this.generation) {
            this.updateAnnotations(response.annotations);

            this.props.onCountsChange(
                response.count_words,
                response.count_sentences,
                response.count_adverb_words,
                response.count_passive_sentences
            );
        }
    }

    updateAnnotations = (annotations: SpanAnnotation[]) => {
        let i = 0;
        let ops: DeltaOperation[] = [];

        // Convert annotations API response to a Delta object
        for (const annotation of annotations) {
            let start = annotation.start;
            let length = annotation.length;

            if (i !== start) {
                // Remove obsolete annotations
                ops.push({retain: start - i, attributes: {passive: null, adverb: null}});
            }

            // Add the new annotation
            ops.push({retain: length, attributes: {[annotation.label]: true}});

            i = start + length;
        }

        const delta = new Delta(ops);
        const editor = this.editorRef.current;
        if (editor !== null) {
            editor.getEditor().updateContents(delta, 'api');
        }
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
            'list', 'direction', 'adverb', 'passive'];

        return <ReactQuill
            theme='snow'
            modules={modules}
            formats={formats}
            onChange={this.onChangeHandler}
            ref={this.editorRef}
        />;
      }
};
