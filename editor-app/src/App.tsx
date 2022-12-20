import { ChakraProvider } from '@chakra-ui/react'
import './App.css';
import { EditorView } from './components/editorview';

function App() {
  return (
    <ChakraProvider>
      <EditorView />
    </ChakraProvider>
  );
}

export default App;
