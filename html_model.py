import dataclasses
from typing import get_args

from bs4 import Tag

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

class Deserializer:
    def __init__(self):
        self.eval_fun = None

    def evaluate_class(self):
        def wrapper(func):
            self.eval_type = func
        return wrapper

    def eval_type(self, cls):
        if not self.eval_fun: raise Exception("Eval function should be defined")
        return self.eval_fun(cls)

    def deserialize(self, input, target_class):
        if input is None: return None
        if not isinstance(input, list) and isinstance(input, target_class): return input

        match input:
            case None:
                return None
            case str():
                return str(input)
            case Tag():
                return self.deserialize_node(input, target_class)
            case list():
                return self.deserialize_list(input, target_class)
            case _:
                raise Exception("Cannot deserialize:" + str(target_class) + " from " + str(input))


    def deserialize_list(self, input, target_class):
        if not isinstance(target_class(), list): raise Exception(str(target_class) + " is not a list")
        type = self.eval_type(get_args(target_class)[0])
        result = []
        for item in input:
            result.append(self.deserialize(item, type))
        return result


    def deserialize_node(self, node: Tag, target_class):
        constructor = {}
        for field in dataclasses.fields(target_class):
            constructor[field.name] = self.deserialize_field(field, node)
        return target_class(**constructor)


    def deserialize_field(self, field: dataclasses.Field, node):
        extractor: Extractor = self.get_extractor(field)
        target_class = field.type
        result = extractor.extract(node)

        return self.deserialize(result, target_class)


    def get_extractor(self, field: dataclasses.Field):
        extractor: Extractor = field.default
        if not isinstance(extractor, Extractor): raise Exception(f"{field.name} does not have an extractor")
        return extractor
