import json
import pytest
from pathlib import Path
from annotate import TextAnnotator

ANALYZE_TEST_CASES = [
    ('A', []),
    ('A ! ,(B)., C / = # %', []),
    ('Tule jo!', [{'start': 5, 'length': 2, 'text': 'jo', 'label': 'adverb'}]),
    #('Koulussa on käytävä.', []),
    ('Koulussa opiskellaan.', [{'start': 9, 'length': 11, 'text': 'opiskellaan', 'label': 'passive'}]),
]

SENTENCE_DIFFICULTY_TEST_CASES = \
    json.load(open(Path(__file__).parent / 'data' / 'difficult_sentences.json'))

annotator = TextAnnotator()


@pytest.mark.parametrize('text,expected_annotations', ANALYZE_TEST_CASES)
def test_annotate_simple_sentences(text, expected_annotations):
    analyzed = annotator.analyze(text)
    assert analyzed.annotations == expected_annotations


@pytest.mark.parametrize('text,difficult_sentences', SENTENCE_DIFFICULTY_TEST_CASES)
def test_sentence_difficulty(text, difficult_sentences):
    doc = annotator.nlp(text)
    annotations = annotator.annotate_difficult_sentences(doc)
    annotated_sentences = [
        doc.text[ann.start:(ann.start + ann.length)]
        for ann in annotations
    ]

    assert annotated_sentences == difficult_sentences
