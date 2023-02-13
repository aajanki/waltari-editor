import spacy
from pydantic import BaseModel
from spacy.matcher import DependencyMatcher
from spacy.symbols import ADJ, ADV, NOUN, VERB
from spacy.tokens import Doc, Span
from typing import Collection, List, Iterable, Tuple


class SpanAnnotation(BaseModel):
    start: int
    length: int
    label: str
    text: str | None


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
        self._initialize_adverb_passive_matcher(self.nlp.vocab)

        # hyphenate function from libvoikko
        lemmatizer_index = self.nlp.pipe_names.index('lemmatizer')
        lemmatizer = self.nlp.pipeline[lemmatizer_index][-1]
        self.hyphenate = lemmatizer.voikko.hyphenate

        # If True, the span text is included in the response to help debugging
        self.debug = False

    def _initialize_adverb_passive_matcher(self, vocab):
        pattern_adverb = [
            {
                "RIGHT_ID": "adverb",
                "RIGHT_ATTRS": {"POS": "ADV"},
            },
        ]
        pattern_passive_verb = [
            {
                "RIGHT_ID": "passive_verb",
                "RIGHT_ATTRS": {
                    "POS": "VERB",
                    "MORPH": {"IS_SUPERSET": ["Voice=Pass", "VerbForm=Fin"]}
                },
            },
        ]
        pattern_passive_aux_verb = [
            {
                "RIGHT_ID": "passive_verb",
                "RIGHT_ATTRS": {
                    "POS": "VERB",
                    "MORPH": {"IS_SUPERSET": ["Voice=Pass"]}
                },
            },
            {
                "LEFT_ID": "passive_verb",
                "REL_OP": ">",
                "RIGHT_ID": "passive_aux",
                "RIGHT_ATTRS": {"POS": "AUX"},
            },
        ]
        self.adverb_passive_matcher = DependencyMatcher(vocab)
        self.matcher_id_adverb = vocab.strings['adverb']
        self.adverb_passive_matcher.add(self.matcher_id_adverb, [pattern_adverb])
        self.matcher_id_passive1 = vocab.strings['passive1']
        self.adverb_passive_matcher.add(self.matcher_id_passive1, [pattern_passive_verb])
        self.matcher_id_passive2 = vocab.strings['passive2']
        self.adverb_passive_matcher.add(self.matcher_id_passive2, [pattern_passive_aux_verb])

    def strip_space(self, sent: Span) -> Span:
        start = 0
        while start < len(sent) and sent[start].is_space:
            start += 1

        end = len(sent) - 1
        while end >= 0 and sent[end].is_space:
            end -= 1

        return sent[start:(end + 1)]

    def annotate_words(self, doc: Doc) -> List[SpanAnnotation]:
        annotations: List[SpanAnnotation] = []
        passive_set = set()
        matches = self.adverb_passive_matcher(doc)
        for (match_id, token_ids) in matches:
            if match_id == self.matcher_id_adverb:
                for i in token_ids:
                    t = doc[i]
                    annotations.append(self.annotation_token(t, 'adverb'))
            else:  # passive
                # Filter out "Alaikäinen voi kirjauduttuaan" type constructs.
                # This is done here because doing it in the matcher is difficult.
                if len(token_ids) > 1 and doc[token_ids[0]].morph.get('Person[psor]'):
                    continue

                passive_set.update(token_ids)

        for start, end in consecutive_ranges(passive_set):
            if end == start + 1:
                annotations.append(self.annotation_token(doc[start], 'passive'))
            else:
                annotations.append(self.annotation_span(doc, start, end, 'passive'))

        return annotations

    def annotate_difficult_sentences(self, doc: Doc) -> List[SpanAnnotation]:
        annotations: List[SpanAnnotation] = []
        for sent in doc.sents:
            word_count = self.count_words(sent)
            if word_count >= 8:
                sent = self.strip_space(sent)
                readability = self.readability(sent)['readability']

                # The bounds below are guesses. The intuition is that the
                # readability score estimates are more unreliable on shorter
                # sentences, and therefore we require a higher readability
                # score before labeling a short sentence.
                #
                # Wiio recommends readability score value 9 as the boundary
                # between normal and difficult texts (on long documents).
                if (
                        (8 <= word_count < 10 and readability > 12.0) or
                        (10 <= word_count < 12 and readability > 10.0) or
                        (word_count >= 12 and readability > 9.0)
                ):
                    annotations.append(
                        self.annotation_span(doc, sent.start, sent.end, 'difficult'))

        return annotations

    def count_sentences(self, doc: Doc, passive_annotations: Iterable[SpanAnnotation]):
        count_sentences = 0
        count_passive_sentences = 0
        passive_starts = sorted([
            x.start for x in passive_annotations if x.label == 'passive'
        ])
        # Append a sentinel value larger that any character position to avoid
        # having to worry about an overflow.
        passive_starts.append(2**64 - 1)

        k = 0
        for sent in doc.sents:
            if all(t.is_space or t.is_punct for t in sent) or (sent.end <= sent.start):
                continue

            count_sentences += 1

            start_token = doc[sent.start]
            start_i = start_token.idx
            end_token = doc[sent.end - 1]
            end_i = end_token.idx + len(end_token)

            while passive_starts[k] < start_i:
                k += 1

            if start_i <= passive_starts[k] < end_i:
                count_passive_sentences += 1

        return count_sentences, count_passive_sentences

    def analyze(self, text: str) -> AnnotationResults:
        doc = self.nlp(text)

        annotations = self.annotate_words(doc)
        annotations = annotations + self.annotate_difficult_sentences(doc)

        count_words = self.count_words(doc)
        count_sents, count_passive_sentences = self.count_sentences(doc, annotations)
        count_adv = sum(1 for x in annotations if x.label == 'adverb')
        readability = self.readability(doc)

        annotations = sorted(annotations, key=lambda x: (x.start, -x.length))

        return AnnotationResults(
            annotations=annotations,
            count_words=count_words,
            count_sentences=count_sents,
            count_passive_sentences=count_passive_sentences,
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

    def annotation_token(self, token, label):
        return SpanAnnotation(
            start=token.idx,
            length=len(token),
            text=token.text if self.debug else None,
            label=label,
        )

    def annotation_span(self, doc, start, end, label):
        if self.debug:
            text = doc[start:end].text
        else:
            text = None

        start_token = doc[start]
        if end > start:
            last_token = doc[end - 1]
            num_chars = last_token.idx + len(last_token) - start_token.idx
        else:
            num_chars = 0

        return SpanAnnotation(
            start=start_token.idx,
            length=num_chars,
            text=text,
            label=label,
        )


def consecutive_ranges(xs: Collection[int]) -> List[Tuple[int, int]]:
    if len(xs) == 0:
        return []

    sorted_xs = sorted(xs)

    ranges = []
    start = sorted_xs[0]
    prev = sorted_xs[0]
    for x in sorted_xs[1:]:
        if x != prev + 1:
            ranges.append((start, prev + 1))
            start = x

        prev = x

    ranges.append((start, prev + 1))

    return ranges
