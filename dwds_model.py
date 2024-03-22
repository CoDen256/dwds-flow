import pprint
import requests
from bs4 import BeautifulSoup
from html_model import *

deserializer = Deserializer()

@deserializer.evaluate_class()
def deserialization_context(cls):
    return eval(cls)


@dataclasses.dataclass
class Lemma:
    text: str = Text()


@dataclasses.dataclass
class Definition:
    text: str = Text()
    pass


@dataclasses.dataclass
class Area:
    text: str = Text()


@dataclasses.dataclass
class Diasystem:
    level: str = Text(NodeByClass("dwdswb-bedeutungsebene"))
    style: str = Text(NodeByClass("dwdswb-stilebene"))
    timeline: str = Text(NodeByClass("dwdswb-gebrauchszeitraum"))
    areas: list['Area'] = NodesByClass("dwdswb-fachgebiet")


@dataclasses.dataclass
# .dwdswb-lesart-def
class Def:
    diasystem: Diasystem = NodeByClass("dwdswb-diasystematik")
    definitions: list['Definition'] = NodesByClass("dwdswb-definition")
    specification: str = Text(NodeByClass("dwdswb-definition-spezifizierung"))
    sytagmatik: str = Text(NodeByClass("dwdswb-syntagmatik"))


@dataclasses.dataclass
class UsageExampleText:
    text: str = Text()


@dataclasses.dataclass
class Phrasem:
    text: str = Text()


@dataclasses.dataclass
# .dwdswb-lesart
class Term:
    id: str = Attribute("id")

    phraseme: list['Phrasem'] = NodeByClass("dwdswb-lesart-content") \
        .then(NodeByClass("dwdswb-phraseme", recursive=False)) \
        .then(NodesByClass("dwdswb-phrasem"))

    definition: Def = NodeByClass("dwdswb-lesart-content") \
        .then(NodeByClass("dwdswb-lesart-def", recursive=False))

    constraint: str = NodeByClass("dwdswb-lesart-content") \
        .then(NodeByClass("dwdswb-ft-la", recursive=False)) \
        .then(NodeByClass("dwdswb-einschraenkung")) \
        .then(Text())

    usages: list['UsageExampleText'] = NodeByClass("dwdswb-lesart-content") \
        .then(NodeByClass("dwdswb-verwendungsbeispiele", recursive=False)) \
        .then(NodesByClass("dwdswb-belegtext"))

    terms: list['Term'] = NodeByClass("dwdswb-lesart-content") \
        .then(NodesByClass("dwdswb-lesart", False))


@dataclasses.dataclass
class Terms:
    terms: list['Term'] = NodesByClass("dwdswb-lesart", recursive=False)

@dataclasses.dataclass
class Result:
    lemma: Lemma = NodeByClass("dwdswb-ft-lemmaansatz")
    terms: Terms = NodeByClass("dwdswb-lesarten")

def main():
    def get_nodes(word, class_):
        text = requests.get(f"https://www.dwds.de/wb/{word}").text
        bs = BeautifulSoup(text, "html.parser")

        return bs.findAll(class_=class_)

    def test_lemma(word):
        return test(word, 0, "dwdswb-ft-lemmaansatz", Lemma)

    def test(word, n, class_, target):
        nodes = get_nodes(word, class_)
        if n >= len(nodes):
            print(str(n) + " is too much")
            return
        node = nodes[n]
        print(word)
        pprint.pprint(deserializer.deserialize(node, target))

    def test_def(word, n):
        test(word, n, "dwdswb-lesart-def", Def)

    def test_term(word, n):
        test(word, n, "dwdswb-lesarten", Terms)

    words = [
        "häufig",
        "Liebe",
        "hallo",
        "vorkommen",
        "auf",
        "aus",
        "mit",
        "inmitten",
        "Mitte",
        "geil",
        "voreingenommen"
        "drauf stehen"
    ]
    for word in words:
        for i in range(1):
            test_term(word, i)
            test_lemma(word)
            # test_def(word, i)


if __name__ == '__main__':
    main()
