import re
import spacy
from pydantic import BaseModel
from spacy.symbols import ADJ, ADV, AUX, NOUN, VERB
from spacy.tokens import Doc, Span
from typing import List


class SpanAnnotation(BaseModel):
    start: int
    length: int
    label: str
    text: str


class AnnotationResults(BaseModel):
    annotations: List[SpanAnnotation]
    count_words: int
    count_sentences: int
    count_adverb_words: int
    count_passive_sentences: int
    readability: float
    readability_long_words: float


class TextAnnotator:
    def __init__(self):
        self.nlp = spacy.load('spacy_fi_experimental_web_md', disable=['ner'])

        # hyphenate function from libvoikko
        lemmatizer_index = self.nlp.pipe_names.index('lemmatizer')
        lemmatizer = self.nlp.pipeline[lemmatizer_index][-1]
        self.hyphenate = lemmatizer.voikko.hyphenate

    def is_passive_voice(self, token):
        morph = token.morph
        return 'Pass' in morph.get('Voice') and 'Part' not in morph.get('VerbForm')

    def is_aux_preceding_passive_verb(self, token):
        # Return true if token and all tokens between it and the token's head are
        # AUX and the head is in passive voice.
        if token.pos == AUX and token.head.pos == VERB and 'Pass' in token.head.morph.get('Voice'):
            for steps_right in range(1, token.head.i - token.i):
                t2 = token.nbor(steps_right)
                if not (t2.pos == AUX and t2.head.i == token.head.i):
                    return False

            return True

        return False

    def strip_space(self, sent: Span) -> Span:
        start = 0
        while start < len(sent) and sent[start].is_space:
            start += 1

        end = len(sent) - 1
        while end >= 0 and sent[end].is_space:
            end -= 1

        return sent[start:(end + 1)]

    def annotation(self, start, text, label):
        return SpanAnnotation(
            start=start,
            length=len(text),
            text=text,
            label=label,
        )

    def annotate_difficult_words(self, doc):
        annotations: List[SpanAnnotation] = []
        count_sents = 0
        count_adv = 0
        count_pass = 0
        processed_i = -1

        sentences = doc.sents
        try:
            next_sentence = next(sentences)
            next_sentence_start_index = next_sentence.start
            if not next_sentence.text.isspace():
                count_sents += 1
        except StopIteration:
            next_sentence_start_index = 0
        passive_sentences = [False]

        for t in doc:
            if t.is_space or t.is_punct:
                continue

            if t.i <= processed_i:
                continue

            if t.i >= next_sentence_start_index:
                try:
                    next_sentence = next(sentences)
                    next_sentence_start_index = next_sentence.start
                    if not next_sentence.text.isspace():
                        count_sents += 1
                    passive_sentences.append(False)
                except StopIteration:
                    pass

            if t.pos == ADV:
                annotations.append(self.annotation(t.idx, t.text, 'adverb'))
                count_adv += 1
                processed_i = t.i
            elif t.pos == AUX and t.head.pos == VERB and 'Pass' in t.head.morph.get('Voice') and not t.head.morph.get('Person[psor]'):
                if self.is_aux_preceding_passive_verb(t):
                    text_span = ''.join(t.nbor(i).text_with_ws for i in range(0, t.head.i - t.i + 1))
                    text_span = re.sub(r'\s*$', '', text_span)
                    annotations.append(self.annotation(t.idx, text_span, 'passive'))
                    processed_i = t.head.i
                else:
                    annotations.append(self.annotation(t.idx, t.text, 'passive'))
                    processed_i = t.i
            elif t.pos == VERB and 'Pass' in t.morph.get('Voice') and not t.morph.get('Person[psor]'):
                is_participle = 'Part' in t.morph.get('VerbForm')
                has_aux = any(x.pos == AUX for x in t.children)
                if (is_participle and has_aux) or not is_participle:
                    annotations.append(self.annotation(t.idx, t.text, 'passive'))
                    count_pass += 1
                    passive_sentences[-1] = True
                    processed_i = t.i
                else:
                    processed_i = t.i
            else:
                processed_i = t.i

        return annotations, count_adv, count_sents, passive_sentences

    def annotate_difficult_sentences(self, doc: Doc) -> List[SpanAnnotation]:
        annotations: List[SpanAnnotation] = []
        for sent in doc.sents:
            sent = self.strip_space(sent)

            if self.count_words(sent) >= 10:
                readability = self.readability(sent)['readability']

                print(f'{readability} -- {sent.text}')

                if readability > 9.0:
                    t = doc[sent.start]
                    annotations.append(
                        self.annotation(t.idx, sent.text, 'difficult_sentence'))

        return annotations

    def analyze(self, text: str) -> AnnotationResults:
        doc = self.nlp(text)

        annotations, count_adv, count_sents, passive_sentences = \
            self.annotate_difficult_words(doc)

        count_words = self.count_words(doc)
        #count_adv = 0
        #count_sents = 0
        #passive_sentences = []
        #annotations = annotations + self.annotate_difficult_sentences(doc)
        readability = self.readability(doc)

        annotations = sorted(annotations, key=lambda x: (x.start, -x.length))

        return AnnotationResults(
            annotations=annotations,
            count_words=count_words,
            count_sentences=count_sents,
            count_passive_sentences=sum(passive_sentences),
            count_adverb_words=count_adv,
            readability=readability['readability'],
            readability_long_words=readability['readability_long_words'],
        )

    def readability(self, doc: Doc | Span) -> dict:
        # Compute readability scores for a text span.
        #
        # Generated two scores that estimate text readability based on the 
        # structural properties of the text. "Readability" is supposed to be
        # more accurate, "readability_long_words" is slightly less accurate,
        # but is simpler to calculate. These are the formulas 9 and 10 from 
        # Osmo A. Wiio: "Readability, comprehension and readership", 1968,
        # pp. 78.
        #
        # The scores quantify the readability as a grade level 1 - 12. Values
        # above 9 are considered "difficult" and values below 6 are "easy".
        count_words = 0
        count_long_words = 0
        count_adj_adv = 0
        count_noun_verb = 0
        word_tokens = (t for t in doc if not (t.is_space or t.is_punct))
        for t in word_tokens:
            count_words += 1

            if self.count_syllables(t.lemma_) >= 4:
                count_long_words += 1

            if t.pos in (ADJ, ADV):
                count_adj_adv += 1
            elif t.pos in (NOUN, VERB):
                count_noun_verb += 1

        if count_noun_verb <= 0:
            modification_ratio = 0.0
        else:
            modification_ratio = 100*count_adj_adv/count_noun_verb

        if count_words < 10:
            # Can't estimate from a short sample
            readability9 = 7.0
            readability10 = 7.0
        else:
            readability9 = 2.7 + 0.3 * count_long_words/count_words*100
            readability10 = 0.7 + 0.3 * count_long_words/count_words*100 \
                + 0.05 * modification_ratio

        return {
            'readability': readability10,
            'readability_long_words': readability9,
        }

    def count_words(self, doc: Doc | Span):
        return sum(1 for t in doc if not (t.is_space or t.is_punct))

    def count_syllables(self, word: str) -> int:
        return self.hyphenate(word).count('-') + 1
