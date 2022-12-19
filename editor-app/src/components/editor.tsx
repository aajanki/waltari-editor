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
    content?: string;
}

export class AnnotatingEditor extends React.Component<IProps, IState> {
    constructor(props: IProps) {
        super(props);
        this.state = {
            content: ''
        };
    }

    onChangeHandler = async (content: string, delta: DeltaStatic, source: string, editor: UnprivilegedEditor) => {
        const response = await fetch("http://localhost:8000/api/hello")
        const helloResponse = await response.json();
        console.log(`on change API response: ${JSON.stringify(helloResponse)}`)

        this.setState({
            content: content
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
