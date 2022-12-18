import re
import spacy
from spacy.symbols import ADV, AUX, VERB

LABEL_COLORS = {
    'ADV': '#7aecec',
    'PASS': '#feca74',
}


class TextAnnotator:
    def __init__(self):
        self.nlp = self.load_nlp()

    def load_nlp(self):
        return spacy.load('spacy_fi_experimental_web_md')

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

    def split_trailing_whitespace(self, text):
        m = re.search(r'\s*$', text)
        if m is None:
            return text, None
        else:
            s = m.start()
            return text[:s], text[s:]

    def annotated_span(self, text, label):
        c = LABEL_COLORS.get(label)
        if c is not None:
            return text, label, c
        else:
            return text, label

    def analyze(self, text):
        def commit_running_text():
            nonlocal running_text, annotated
            if running_text:
                annotated.append(''.join(running_text))
                running_text = []

        def append_annotated(text, label):
            nonlocal running_text

            commit_running_text()

            text_no_ws, trailing_ws = self.split_trailing_whitespace(text)
            annotated.append(self.annotated_span(text_no_ws, label))

            if trailing_ws is not None:
                running_text.append(trailing_ws)

        annotated = []
        running_text = []
        count_words = 0
        count_sents = 0
        count_adv = 0
        count_pass = 0
        processed_i = -1

        doc = self.nlp(text)
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
            if t.is_space:
                running_text.append(t.text_with_ws)
                continue

            count_words += 1

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
                append_annotated(t.text_with_ws, 'ADV')
                count_adv += 1
                processed_i = t.i
            elif t.pos == AUX and t.head.pos == VERB and 'Pass' in t.head.morph.get('Voice') and not t.head.morph.get('Person[psor]'):
                if self.is_aux_preceding_passive_verb(t):
                    text_span = ''.join(t.nbor(i).text_with_ws for i in range(0, t.head.i - t.i + 1))
                    append_annotated(text_span, 'PASS')
                    processed_i = t.head.i
                else:
                    append_annotated(t.text_with_ws, 'PASS')
                    processed_i = t.i
            elif t.pos == VERB and 'Pass' in t.morph.get('Voice') and not t.morph.get('Person[psor]'):
                is_participle = 'Part' in t.morph.get('VerbForm')
                has_aux = any(x.pos == AUX for x in t.children)
                if (is_participle and has_aux) or not is_participle:
                    append_annotated(t.text_with_ws, 'PASS')
                    count_pass += 1
                    passive_sentences[-1] = True
                    processed_i = t.i
            else:
                running_text.append(t.text_with_ws)
                processed_i = t.i

        commit_running_text()

        return {
            'annotated': annotated,
            'count_sentences': count_sents,
            'count_words': count_words,
            'count_pass': sum(passive_sentences),
            'count_adv': count_adv,
        }
