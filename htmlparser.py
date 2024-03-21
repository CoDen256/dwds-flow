import dataclasses
from typing import get_args

import requests
from bs4 import BeautifulSoup, Tag


def get_nodes(word, class_):
    text = requests.get(f"https://www.dwds.de/wb/{word}").text
    bs = BeautifulSoup(text, "html.parser")

    return bs.findAll(class_=class_)

class Extractor:
    def extract(self, node: Tag):
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
            raise Exception("Cannot deserialize:"+str(target_class)+" from "+str(input))


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


class NodeByClass(Extractor):
    def __init__(self, class_):
        self.class__ = class_

    def __repr__(self):
        return "class='" + self.class__ + "'"

    def extract(self, node: Tag):
        return node.find(class_=self.class__)


class NodesByClass(Extractor):
    def __init__(self, class_):
        self.class__ = class_

    def __repr__(self):
        return "class='" + self.class__ + "'"

    def extract(self, node: Tag):
        return list(node.findAll(class_=self.class__))


class Text(Extractor):
    def __init__(self):
        pass

    def extract(self, node: Tag):
        return node.text


class Self(Extractor):
    def __init__(self):
        pass

    def extract(self, node: Tag):
        return node


@dataclasses.dataclass
class Diasystem:
    # node: Tag = Self()
    text: str = Text()

@dataclasses.dataclass
class Definition:
    # node: Tag = Self()
    text: str = Text()
    pass


@dataclasses.dataclass
class Definitions:
    # node: Tag = Self()
    definitions: list['Definition'] = NodesByClass("dwdswb-definition")


@dataclasses.dataclass
class Def:
    # node: Tag = Self()
    diasystem: Diasystem = NodeByClass("dwdswb-diasystematik")
    definitions: Definitions = NodeByClass("dwdswb-definitionen")


def test_def(word, n):
    nodes = get_nodes(word, "dwdswb-lesart-def")
    if n >= len(nodes):
        print(str(n) + " is too much")
        return
    node = nodes[n]
    print(word, deserialize(node, Def))

if __name__ == '__main__':
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
        "Voreingenommenheit"
             ]
    for i in range(1):
        for word in words:
            test_def(word, i)