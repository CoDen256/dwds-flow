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
        return self.extract_single(node)

    def extract_single(self, node: Tag):
        pass

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
    def __init__(self, cls, prev: Extractor = None):
        super().__init__(prev)
        self.cls = cls

    def extract_single(self, node: Tag):
        return node.find(class_=self.cls)


class NodesByClass(Extractor):
    def __init__(self, cls, prev: Extractor = None):
        super().__init__(prev)
        self.cls = cls

    def __repr__(self):
        return "class='" + self.cls + "'"

    def extract_single(self, node: Tag):
        return list(node.findAll(class_=self.cls))


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
class Diasystem:
    # node: Tag = I()
    text: str = Text()


@dataclasses.dataclass
class Definition:
    # node: Tag = I()
    text: str = Text()
    pass


@dataclasses.dataclass
class Definitions:
    # node: Tag = I()
    definitions: list['Definition'] = NodesByClass("dwdswb-definition")


@dataclasses.dataclass
class Def:
    # node: Tag = I()
    diasystem: Diasystem = NodeByClass("dwdswb-diasystematik")
    definitions: Definitions = NodeByClass("dwdswb-definitionen")


@dataclasses.dataclass
class UsageExampleText:
    text: str = Text()


@dataclasses.dataclass
class Term:
    id: str = Attribute("id")
    definition: Def = NodeByClass("dwdswb-lesart-def")
    usages: list['UsageExampleText'] = NodesByClass("dwdswb-belegtext")


@dataclasses.dataclass
class Terms:
    terms: list['Term'] = NodesByClass("dwdswb-lesart")


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
        # "Liebe",
        # "hallo",
        # "vorkommen",
        # "auf",
        # "aus",
        # "mit",
        # "inmitten",
        # "Mitte",
        "geil"
    ]
    for word in words:
        for i in range(1):
            test_term(word, i)
            # test_def(word, i)
