import { Box, Card, CardBody, Flex, Text } from '@chakra-ui/react'

interface AnnotationSidebarProps {
    count_words: number
    count_sentences: number
    count_adverb_words: number,
    count_passive_sentences: number,
    readability: number,
    readability2: number,
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
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_sentences} virkettä</Text>
                    </CardBody>
                </Card>
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_passive_sentences} passiivivirkettä</Text>
                    </CardBody>
                </Card>
                <Card variant='outline'>
                    <CardBody>
                    <Text>{props.count_adverb_words} seikkasanaa</Text>
                    </CardBody>
                </Card>
                <Card variant='outline'>
                    <CardBody>
                    <Text>Luettavuus (luokkataso): {props.readability.toFixed(1)}</Text>
                    </CardBody>
                </Card>
                <Card variant='outline'>
                    <CardBody>
                    <Text>Luettavuus, pitkät sanat: {props.readability2.toFixed(1)}</Text>
                    </CardBody>
                </Card>
            </Flex>
        </Box>
    );
}
