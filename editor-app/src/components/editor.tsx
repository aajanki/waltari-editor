import React from 'react';
import ReactQuill, { Quill, UnprivilegedEditor } from 'react-quill';
import { DeltaStatic } from 'quill';
import 'react-quill/dist/quill.snow.css';

let Inline = Quill.import('blots/inline');
class AnnotatedBlot extends Inline {}
AnnotatedBlot.blotName = 'annotate';
AnnotatedBlot.tagName = 'mark';
Quill.register('formats/annotate', AnnotatedBlot);

interface IProps {
};

interface IState {
    content: string;
    count_words: number,
    count_sentences: number,
    count_adverb_words: number,
    count_passive_sentences: number,
};

export class AnnotatingEditor extends React.Component<IProps, IState> {
    constructor(props: IProps) {
        super(props);
        this.state = {
            content: '',
            count_words: 0,
            count_sentences: 0,
            count_adverb_words: 0,
            count_passive_sentences: 0,
        };
    }

    onChangeHandler = async (content: string, delta: DeltaStatic, source: string, editor: UnprivilegedEditor) => {
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
        console.log(response);

        this.setState({
            content: content,
            count_words: response.count_words,
            count_sentences: response.count_sentences,
            count_adverb_words: response.count_adverb_words,
            count_passive_sentences: response.count_passive_sentences,
        });
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
            value={this.state.content}
            onChange={this.onChangeHandler} />;
      }
};
