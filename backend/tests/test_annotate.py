import pytest
from annotate import TextAnnotator


SIMPLE_TEST_CASES = [
    'A',
    'A ! ,(B)., C / = # %',
    'Tule jo!',
    'Koulussa on käytävä.',
    'Koulussa opiskellaan.',
    'Kolme poikaa kävel',
    'Kolme poikaa käveli',
    'Kolme poikaa käveli kadulla.',
]

annotator = TextAnnotator()


def get_text(annotation_result):
    delta = annotation_result['delta']
    return ''.join(x.get('insert', '') for x in delta)


@pytest.mark.parametrize('text', SIMPLE_TEST_CASES)
def test_keeps_plain_text(text):
    analyzed = annotator.analyze(text)
    assert get_text(analyzed) == text
