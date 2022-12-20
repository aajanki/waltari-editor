import { Box, Card, CardBody, Flex, Spacer, Text } from '@chakra-ui/react'

interface AnnotationSidebarProps {
    count_words: number
    count_sentences: number
    count_adverb_words: number,
    count_passive_sentences: number,
}

export function AnnotationSidebar(props: AnnotationSidebarProps) {
    return (
        <Box h='full' w='15%' maxW='25ch'>
            <Flex direction='column' gap='4px'>
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_words} sanaa</Text>
                    </CardBody>
                </Card>
                <Spacer />
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_sentences} lausetta</Text>
                    </CardBody>
                </Card>
                <Spacer />
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_passive_sentences} passiivilausetta</Text>
                    </CardBody>
                </Card>
                <Spacer />
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_adverb_words} seikkasanaa</Text>
                    </CardBody>
                </Card>
            </Flex>
        </Box>
    );
}
