import React from 'react';
import { AnnotatingEditor } from './editor'
import { AnnotationSidebar } from './sidebar'
import { Container, Stack } from '@chakra-ui/react'

interface EditorViewProps {}

interface EditorViewState {
    count_words: number,
    count_sentences: number,
    count_adverb_words: number,
    count_passive_sentences: number,
    readability: number,
}

export class EditorView extends React.Component<EditorViewProps, EditorViewState> {
    constructor(props: EditorViewProps) {
        super(props);

        this.state = {
            count_words: 0,
            count_sentences: 0,
            count_adverb_words: 0,
            count_passive_sentences: 0,
            readability: 0,
        }
    }

    onCountChange = (words: number, sentences: number, adverbs: number, passives: number, readability: number) => {
        this.setState({
            count_words: words,
            count_sentences: sentences,
            count_adverb_words: adverbs,
            count_passive_sentences: passives,
            readability: readability,
        })
    }

    render() {
        return (
            <Stack direction='row'>
                <Container centerContent height='50ch' maxWidth='80ch'>
                    <AnnotatingEditor onCountsChange={this.onCountChange} />
                </Container>
                <AnnotationSidebar
                    count_words={this.state.count_words}
                    count_sentences={this.state.count_sentences}
                    count_adverb_words={this.state.count_adverb_words}
                    count_passive_sentences={this.state.count_passive_sentences}
                    readability={this.state.readability}
                />
            </Stack>
        );
    }
}