import dataclasses
import json
import typing

import requests
from bs4 import BeautifulSoup


@dataclasses.dataclass(init=False)
class DefinedTerm:
    description: str

    def __init__(self, description, **kwargs):
        self.description = description


@dataclasses.dataclass(init=False)
class Quotation:
    text: str

    def __init__(self, text, **kwargs):
        self.text = text


@dataclasses.dataclass
class Term:
    definition: str
    examples: typing.List[str]
    subterms: typing.List['Term']


class DWDSConnector:
    DWDS_URL = "https://www.dwds.de/wb/{query}"

    def __init__(self):
        pass

    def fetch_page(self, query):
        url = DWDSConnector.DWDS_URL.format(query=query)
        return requests.get(url).text


class DWDSParser(BeautifulSoup):
    PREFIX = "dwdswb-"

    def __init__(self, page):
        super().__init__(page, 'html.parser')
        self.page = page

    @staticmethod
    def find_script_with_terms(scripts):
        for s in scripts:
            if "DefinedTerm" in s.text:
                return json.loads(s.text)

    def fetch_scripts(self):
        return self.findAll("script")

    def parse_defined_terms_and_quotations(self):
        scripts = self.fetch_scripts()
        relevant = self.find_script_with_terms(scripts)
        if (not relevant): return [], []
        return list(self.parse_quotations(relevant)), list(self.parse_defined_terms(relevant))

    @staticmethod
    def parse_quotations(content):
        for obj in content:
            if obj["@type"] == "Quotation":
                yield Quotation(**obj)

    @staticmethod
    def parse_defined_terms(content):
        for obj in content:
            if obj["@type"] == "DefinedTerm":
                yield DefinedTerm(**obj)

    @staticmethod
    def find_one(root, postfix):
        return root.find(class_=DWDSParser.PREFIX + postfix, recursive=False)

    @staticmethod
    def find_many(root, postfix):
        return root.findAll(class_=DWDSParser.PREFIX + postfix, recursive=False)

    def parse_main_terms(self):
        root = self.find(class_=DWDSParser.PREFIX + "lesarten")
        if not root: return []
        return self.parse_children(root)

    def parse_children(self, root):
        children = self.find_many(root, "lesart")
        result = []
        for child in children:
            result.append(self.parse_term(child))
        return result

    def parse_term(self, root):
        root = self.find_one(root, "lesart-content")
        if not root: return None

        definition = self.parse_definition(root)
        examples = self.parse_examples(root)
        children = self.parse_children(root)
        return Term(definition=definition, examples=examples, subterms=children)

    def parse_definition(self, root):
        return self.find_one(root, "lesart-def").text

    def parse_examples(self, root):
        examples_root = self.find_one(root, "verwendungsbeispiele")
        if not examples_root: return []

        children = self.find_many(examples_root, "kompetenzbeispiel")
        result = []
        for child in children:
            example = self.find_one(child, "belegtext")
            result.append(example.text)
        return result


def parse_dwds_terms(query):
    page = DWDSConnector().fetch_page(query)
    return DWDSParser(page).parse_main_terms()


def parse_dwds_terms_reduced(query):
    page = DWDSConnector().fetch_page(query)
    dwds_parser = DWDSParser(page)
    return dwds_parser.parse_defined_terms_and_quotations()
