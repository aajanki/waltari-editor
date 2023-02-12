import json
import pytest
from pathlib import Path
from annotate import TextAnnotator

ANALYZE_TEST_CASES = [
    (
        'A',
        [],
        {
            'words': 1,
            'sentences': 1,
            'passives': 0,
            'adverbs': 0,
        }
    ),
    (
        'A ! ,(B)., C / = # %',
        [],
        {
            'words': 4,
            'sentences': 1,
            'passives': 0,
            'adverbs': 0,
        }
    ),
    (
        'Tule jo!',
        [{'start': 5, 'length': 2, 'text': None, 'label': 'adverb'}],
        {
            'words': 2,
            'sentences': 1,
            'passives': 0,
            'adverbs': 1,
        }
    ),
    (
        'Koulussa opiskellaan kieliä.',
        [{'start': 9, 'length': 11, 'text': None, 'label': 'passive'}],
        {
            'words': 3,
            'sentences': 1,
            'passives': 1,
            'adverbs': 0,
        }
    ),
    (
        'Tutkitaan asiaa!',
        [{'start': 0, 'length': 9, 'text': None, 'label': 'passive'}],
        {
            'words': 2,
            'sentences': 1,
            'passives': 1,
            'adverbs': 0,
        }
    ),
    (
        'Jutta käy kerhossa iltapäivisin. Kerhossa leikitään sopuisasti.',
        [
            {'start': 19, 'length': 12, 'text': None, 'label': 'adverb'},
            {'start': 42, 'length': 9, 'text': None, 'label': 'passive'},
            {'start': 52, 'length': 10, 'text': None, 'label': 'adverb'},
        ],
        {
            'words': 7,
            'sentences': 2,
            'passives': 1,
            'adverbs': 2,
        }
    ),
]

SENTENCE_DIFFICULTY_TEST_CASES = \
    json.load(open(Path(__file__).parent / 'data' / 'difficult_sentences.json'))

PASSIVE_TEST_CASES = \
    json.load(open(Path(__file__).parent / 'data' / 'passive.json'))

annotator = TextAnnotator()


def test_annotate_empty_string():
    analyzed = annotator.analyze('')

    assert len(analyzed.annotations) == 0
    assert analyzed.count_words == 0
    assert analyzed.count_sentences == 0
    assert analyzed.count_passive_sentences == 0
    assert analyzed.count_adverb_words == 0


@pytest.mark.parametrize('text,expected_annotations,expected_counts', ANALYZE_TEST_CASES)
def test_annotate(text, expected_annotations, expected_counts):
    analyzed = annotator.analyze(text)

    assert analyzed.annotations == expected_annotations
    assert analyzed.count_words == expected_counts['words']
    assert analyzed.count_adverb_words == expected_counts['adverbs']
    assert analyzed.count_sentences == expected_counts['sentences']
    assert analyzed.count_passive_sentences == expected_counts['passives']


@pytest.mark.parametrize('text,difficult_sentences', SENTENCE_DIFFICULTY_TEST_CASES)
def test_sentence_difficulty(text, difficult_sentences):
    doc = annotator.nlp(text)
    annotations = annotator.annotate_difficult_sentences(doc)
    annotated_sentences = [
        doc.text[ann.start:(ann.start + ann.length)]
        for ann in annotations
    ]

    assert annotated_sentences == difficult_sentences


@pytest.mark.parametrize('text,expected_passives', PASSIVE_TEST_CASES)
def test_passive(text, expected_passives):
    doc = annotator.nlp(text)
    annotations = annotator.analyze(doc).annotations
    observed_passives = [
        doc.text[ann.start:(ann.start + ann.length)]
        for ann in annotations
        if ann.label == 'passive'
    ]

    assert observed_passives == expected_passives
