import dataclasses
import pprint
from typing import get_args

import requests
from bs4 import BeautifulSoup, Tag


def get_nodes(word, class_):
    text = requests.get(f"https://www.dwds.de/wb/{word}").text
    bs = BeautifulSoup(text, "html.parser")

    return bs.findAll(class_=class_)


class Extractor:
    def __init__(self, prev: 'Extractor' = None):
        self.prev = prev

    def extract(self, node: Tag):
        if self.prev:
            node = self.prev.extract(node)

        if node is None:
            return None

        return self.extract_single(node)

    def extract_single(self, node: Tag):
        pass

    def then(self, next: 'Extractor'):
        next.prev = self
        return next

def deserialize_list(input, target_class):
    if not isinstance(target_class(), list): raise Exception(str(target_class) + " is not a list")
    type = eval(get_args(target_class)[0])
    result = []
    for item in input:
        result.append(deserialize(item, type))
    return result


def deserialize(input, target_class):
    if input is None: return None
    if not isinstance(input, list) and isinstance(input, target_class): return input

    match input:
        case None:
            return None
        case str():
            return str(input)
        case Tag():
            return deserialize_node(input, target_class)
        case list():
            return deserialize_list(input, target_class)
        case _:
            raise Exception("Cannot deserialize:" + str(target_class) + " from " + str(input))


def deserialize_node(node: Tag, target_class):
    constructor = {}
    for field in dataclasses.fields(target_class):
        constructor[field.name] = deserialize_field(field, node)
    return target_class(**constructor)


def deserialize_field(field: dataclasses.Field, node):
    extractor: Extractor = get_extractor(field)
    target_class = field.type
    result = extractor.extract(node)

    return deserialize(result, target_class)


def get_extractor(field: dataclasses.Field):
    extractor: Extractor = field.default
    if not isinstance(extractor, Extractor): raise Exception(f"{field.name} does not have an extractor")
    return extractor


class I(Extractor):
    def __init__(self, prev: Extractor = None):
        super().__init__(prev)

    def extract_single(self, node: Tag):
        return node

class NodeByClass(Extractor):
    def __init__(self, cls, recursive=True, prev: Extractor = None):
        super().__init__(prev)
        self.cls = cls
        self.recursive = recursive

    def extract_single(self, node: Tag):
        return node.find(class_=self.cls, recursive=self.recursive)


class NodesByClass(Extractor):
    def __init__(self, cls, recursive=True, prev: Extractor = None):
        super().__init__(prev)
        self.cls = cls
        self.recursive = recursive

    def __repr__(self):
        return "class='" + self.cls + "'"

    def extract_single(self, node: Tag):
        return list(node.findAll(class_=self.cls, recursive=self.recursive))


class Attribute(Extractor):
    def __init__(self, attribute, prev: Extractor = None):
        super().__init__(prev)
        self.attribute = attribute

    def extract_single(self, node: Tag):
        if not node.has_attr(self.attribute): return None
        return node.attrs[self.attribute]


class Text(Extractor):
    def __init__(self, prev: Extractor = None):
        super().__init__(prev)

    def extract_single(self, node: Tag):
        return node.text


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

    phraseme: list['Phrasem'] = NodeByClass("dwdswb-lesart-content")\
                                .then(NodeByClass("dwdswb-phraseme", recursive=False))\
                                .then(NodesByClass("dwdswb-phrasem"))

    definition: Def = NodeByClass("dwdswb-lesart-content")\
                            .then(NodeByClass("dwdswb-lesart-def", recursive=False))

    constraint: str = NodeByClass("dwdswb-lesart-content") \
                            .then(NodeByClass("dwdswb-ft-la", recursive=False)) \
                            .then(NodeByClass("dwdswb-einschraenkung")) \
                            .then(Text())

    usages: list['UsageExampleText'] = NodeByClass("dwdswb-lesart-content")\
                                        .then(NodeByClass("dwdswb-verwendungsbeispiele", recursive=False))\
                                        .then(NodesByClass("dwdswb-belegtext"))

    terms: list['Term'] = NodeByClass("dwdswb-lesart-content")\
                            .then(NodesByClass("dwdswb-lesart", False))

@dataclasses.dataclass
class Terms:
    terms: list['Term'] = NodesByClass("dwdswb-lesart", recursive=False)

def test(word, n, class_, target):
    nodes = get_nodes(word, class_)
    if n >= len(nodes):
        print(str(n) + " is too much")
        return
    node = nodes[n]
    print(word)
    pprint.pprint(deserialize(node, target))


def test_def(word, n):
    test(word, n, "dwdswb-lesart-def", Def)


def test_term(word, n):
    test(word, n, "dwdswb-lesarten", Terms)


if __name__ == '__main__':
    words = [
        # "häufig",
        "Liebe",
        # "hallo",
        # "vorkommen",
        # "auf",
        # "aus",
        # "mit",
        # "inmitten",
        # "Mitte",
        # "geil"
        # "voreingenommen"
    ]
    for word in words:
        for i in range(1):
            test_term(word, i)
            # test_def(word, i)
