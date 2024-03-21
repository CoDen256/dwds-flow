import dataclasses

import html_to_json
import requests
from bs4 import BeautifulSoup, PageElement, Tag

text = requests.get("https://www.dwds.de/wb/h%C3%A4ufig").text
bs = BeautifulSoup(text, "html.parser")

node = bs.findAll(class_="dwdswb-diasystematik")[0]
print(node)


class Extractor:
    def extract(self, node: Tag) -> Tag:
        pass


def deserialize(input, target_class):
    match input:
        case str():
            return str(input)
        case Tag():
            return deserialize_node(input, target_class)


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


class Text(Extractor):
    def __init__(self):
        pass

    def extract(self, node: Tag):
        return node.text


@dataclasses.dataclass
class Timeline:
    text: str = Text()


@dataclasses.dataclass
class Definition:
    gebrauchszeitraum: Timeline = NodeByClass("dwdswb-gebrauchszeitraum")


# print(Definition(""))
# print([0].type)

print(deserialize(node, Definition))
