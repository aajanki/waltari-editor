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

READABLE_SENTENCES = [
    "Tyttö lukee hauskaa satukirjaa, joka kertoo kiltistä norsusta.",
    "Ongelma on myös se, että kaikki suomalaiset eivät saa yhtä hyviä terveyspalveluja.",
    "Hyvinvointialueilla sosiaalityöntekijät, lääkärit, terveydenhoitajat ja sairaanhoitajat työskentelevät yhdessä.",
    "Tavoite on, että vanhukset saavat paremmin esimerkiksi päihdeongelmiin ja mielenterveyteen liittyviä palveluita.",
    "Jos teemme virheitä projektin toteutuksessa, aikataulu saattaa venyä, joten on tärkeää suorittaa toimenpiteet oikein ja ajoissa.",
    "Tässä on muutamia käytännön vinkkejä, jotka auttavat sinua parantamaan liiketoimintasi kannattavuutta ja kilpailukykyä.",
    "Ei tarvitse kuin muistella Ruotsin poliittista historiaa toisen maailmansodan ja kylmän sodan aikana.",
]

CHALLENGING_SENTENCES = [
    "Perustamissäädösten säännökset säilyisivät prosessoitavassa muutoksessa pitkälti ennallaan poronhoidon edellytysten osalta.",
    "Organisaatiomme kiittää mahdollisuudesta antaa lausunto hallituksen esityksestä eduskunnalle laiksi EU-ympäristömerkinnästä annetun lain muuttamisesta.",
    "Filosofian kandidaatti tarkastelee kriittisesti pohdiskelevaa tutkimusartikkelia fenomaalisen tietoisuuden selittämisestä neurologisilla tekijöillä.",
    "Norjalainen teräsfirma Blastr Green Steel suunnittelee terästehdasta ja integroidun vedyn tuotantolaitosta Inkooseen.",
    "Tämän konseptin yksityiskohtainen analysointi on välttämätöntä, jotta voidaan arvioida sen vaikutusta liiketoimintastrategiaan.",
    "Osakassopimus on oikeustoimi, jolla osakkeenomistajat sopivat keskenään yhtiön hallinnosta ja osakkeenomistajien välisistä suhteista.",
    "Uusi seuraamusmaksu, myöhästymismaksu, korvaa veronkorotuksen eräissä tilanteissa, joissa veroilmoitus on annettu myöhässä tai verovelvollinen täydentää tai korjaa autoverotuksen perusteena käytettyjä ajoneuvotietoja myöhässä.",
]

READABILITY_LONG_TEXT_TEST_CASES = \
    json.load(open(Path(__file__).parent / 'data' / 'readability.json'))

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


@pytest.mark.parametrize('text,difficult_sentences', READABILITY_LONG_TEXT_TEST_CASES)
def test_text_readability(text, difficult_sentences):
    doc = annotator.nlp(text)
    annotations = annotator.annotate_difficult_sentences(doc)
    annotated_sentences = [
        doc.text[ann.start:(ann.start + ann.length)]
        for ann in annotations
    ]

    assert annotated_sentences == difficult_sentences


@pytest.mark.parametrize('text', READABLE_SENTENCES)
def test_readable_sentences(text):
    doc = annotator.nlp(text)
    annotations = annotator.annotate_difficult_sentences(doc)
    annotations = [x for x in annotations if x.label == 'difficult']

    assert len(annotations) == 0


@pytest.mark.parametrize('text', CHALLENGING_SENTENCES)
def test_challenging_sentences(text):
    doc = annotator.nlp(text)
    annotations = annotator.annotate_difficult_sentences(doc)
    annotations = [x for x in annotations if x.label == 'difficult']

    assert len(annotations) > 0


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
