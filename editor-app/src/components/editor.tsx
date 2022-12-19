import { useState } from 'react';
import ReactQuill, { Quill } from 'react-quill';
import 'react-quill/dist/quill.snow.css';

let Inline = Quill.import('blots/inline');
class AnnotatedBlot extends Inline {}
AnnotatedBlot.blotName = 'annotate';
AnnotatedBlot.tagName = 'mark';
Quill.register('formats/annotate', AnnotatedBlot);

export function AnnotatingEditor() {
  const [value, setValue] = useState('');

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
    value={value}
    onChange={setValue} />;
}
