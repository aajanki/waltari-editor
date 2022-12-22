import React from 'react';
import ReactQuill, { Quill, UnprivilegedEditor } from 'react-quill';
import { DeltaStatic } from 'quill';
import 'react-quill/dist/quill.snow.css';

let Inline = Quill.import('blots/inline');
class AnnotatedBlot extends Inline {}
AnnotatedBlot.blotName = 'annotate';
AnnotatedBlot.tagName = 'mark';
Quill.register('formats/annotate', AnnotatedBlot);

interface AnnotatingEditorProps {
    onCountsChange: (words: number, sentences: number, adverbs: number, passives: number) => void
}

interface AnnotatingEditorState {
    value: any // FIXME
}

export class AnnotatingEditor extends React.Component<AnnotatingEditorProps, AnnotatingEditorState> {
    constructor(props: AnnotatingEditorProps) {
        super(props);

        this.state = {
            value: ''
        };
    }

    onChangeHandler = async (content: string, delta: DeltaStatic, source: string, editor: UnprivilegedEditor) => {
        if (source !== 'user') {
            this.setState({value: editor.getContents()});
            return;
        }

        const contents = editor.getContents();

        const requestBody = {
            delta: contents
        };
        const rawResponse = await fetch('/api/annotate', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        const response = await rawResponse.json();

        this.setState({value: response.delta});
        this.props.onCountsChange(
            response.count_words,
            response.count_sentences,
            response.count_adverb_words,
            response.count_passive_sentences
        );
    }

    render() {
        const modules = {
            toolbar: [
                ['bold', 'italic', 'underline'],
                [{'list': 'ordered'}, {'list': 'bullet'}]
            ]
        };
        const formats = [
            'bold', 'font', 'italic', 'annotate', 'link', 'size', 'underline', 'indent',
            'list', 'direction'];

        return <ReactQuill
            theme='snow'
            modules={modules}
            formats={formats}
            value={this.state.value}
            onChange={this.onChangeHandler} />;
      }
};
