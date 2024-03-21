import dataclasses
from typing import List
from typing import TypeVar, Generic, get_args

import html_to_json
import requests
from bs4 import BeautifulSoup, PageElement, Tag

text = requests.get("https://www.dwds.de/wb/h%C3%A4ufig").text
bs = BeautifulSoup(text, "html.parser")

node = bs.findAll(class_="dwdswb-definitionen")[0]
print(node)


class Extractor:
    def extract(self, node: Tag):
        pass


def deserialize_list(input, target_class):
    type = eval(get_args(target_class)[0])
    result = []
    for item in input:
        result.append(deserialize(item, type))
    return result


def deserialize(input, target_class):
    if not isinstance(input, list) and isinstance(input, target_class): return input

    match input:
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
    node = extractor.extract(node)

    return deserialize(node, target_class)


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
class Timeline:
    node: Tag = Self()
    text: str = Text()


@dataclasses.dataclass
class Definition:
    node: Tag = Self()
    gebrauchszeitraum: Timeline = NodeByClass("dwdswb-gebrauchszeitraum")


@dataclasses.dataclass
class Definitions:
    node: Tag = Self()
    definitions: list['Def'] = NodesByClass("dwdswb-definition")


@dataclasses.dataclass
class Def:
    node: Tag = Self()
    pass

# print(Definition(""))
# print([0].type)

s = deserialize(node, Definitions)
print(s)
