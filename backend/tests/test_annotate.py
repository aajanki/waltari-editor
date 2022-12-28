import pytest
from annotate import TextAnnotator

TEST_CASES = [
    ('A', []),
    ('A ! ,(B)., C / = # %', []),
    ('Tule jo!', [{'start': 5, 'length': 2, 'text': 'jo', 'label': 'adverb'}]),
    #('Koulussa on käytävä.', []),
    ('Koulussa opiskellaan.', [{'start': 9, 'length': 11, 'text': 'opiskellaan', 'label': 'passive'}]),
]

annotator = TextAnnotator()

@pytest.mark.parametrize('text,expected_annotations', TEST_CASES)
def test_simple_sentences(text, expected_annotations):
    analyzed = annotator.analyze(text)
    assert analyzed['annotations'] == expected_annotations
