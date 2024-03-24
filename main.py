# -*- coding: utf-8 -*-
import dataclasses
import os
import pprint
import re
import sys
import time
from typing import List

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from dwds_model import Result, Term, Def, Terms, Phrasem, UsageExampleText, Definition, Area
from flowlauncher import FlowLauncher
from dwds import parse_dwds_result
import webbrowser


@dataclasses.dataclass
class QueryResult:
    title: str
    subtitle: str
    id: str


class DWDSSearcher(FlowLauncher):

    def query(self, param):
        return list(self.generate_results(param))

    def generate_results(self, query):
        if len(query) <= 1: return []
        if len(query) <= 4:
            time.sleep(0.3)
        with open("log", "a") as f:
            f.write("queried: " + query + "\n")
        result = parse_dwds_result(query)
        for result in self.transform(query, result):
            id = '' if not result.id or len(result.id) < 5 else result.id[4:5] + '. '
            yield {
                "Title": id + result.title,
                # max 60 x 2
                "SubTitle": self.clean_subtitle(result.subtitle, 85),
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": [self.link(query, result.id)]
                }
            }

    def clean_subtitle(self, title, break_index):
        return self.soft_break_after(title, break_index).strip()

    def soft_break_after(self, text, max):
        result = ""
        indented = False
        for word in text.split(" "):
            if not indented and len(result) + len(word) > max:
                result += "\n" + word
                indented = True
            else:
                result += " " + word
        return result

    def context_menu(self, data):
        return [
            {
                "Title": data[0],
                "SubTitle": "Press enter to open Flow the plugin's repo in GitHub\n" * 10,
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": ["https://github.com/Flow-Launcher/Flow.Launcher.Plugin.HelloWorldPython"]
                }
            }
        ]

    def open_url(self, url):
        webbrowser.open(url)

    def link(self, word, id=None):
        return "https://www.dwds.de/wb/" + word + "#" + ("" if not id else id)

    def transform(self, orig, result: Result):

        if result.lemma and result.lemma.text:  # and orig.strip() != result.lemma.text:
            yield QueryResult(title=result.lemma.text, subtitle="", id=None)

        result_terms = self.map_to_results(result.terms)

        for term in result_terms:
            for result in self.generate_definition_and_examples(term):
                yield result

    def generate_definition_and_examples(self, term: 'ResultTerm', parent_term: 'ResultTerm' = None):
        phrasem = self.generate_phrasem(term)
        definition = self.generate_definition(term.definition)
        fallback = self.fallback_definition(term.definition, parent_term)
        actual_definition = definition if definition else fallback

        result = self.add_phrasem_if_exists(actual_definition, phrasem)

        examples = list(self.generate_examples(term, 1))

        for example in examples:
            yield QueryResult(title=result, subtitle=example, id=term.id)

        if not examples and (definition or phrasem):
            result = self.add_phrasem_if_exists(definition, phrasem)
            yield QueryResult(title=result, subtitle='', id=term.id)

        for current in term.subterms:
            for sub_result in self.generate_definition_and_examples(current, term):
                yield sub_result

    def add_phrasem_if_exists(self, actual_definition, phrasem):
        if phrasem:
            if '=' in phrasem:
                return phrasem
            else:
                return phrasem + ' = ' + actual_definition
        return actual_definition

    def generate_phrasem(self, term: 'ResultTerm'):
        if term.phrasems:
            return term.phrasems[0]

    def generate_definition(self, definition: 'ResultDefinition') -> str:
        # Redewedung, figuratively (= explanation)
        if definition.definitions:
            return "; ".join(definition.definitions)
        if definition.specification:
            return definition.specification

        if definition.constraint:
            return definition.constraint

        return None

    def fallback_definition(self, definition: 'ResultDefinition', parent_definition: 'ResultTerm'):
        extra = []
        if definition.sytagmatic:
            extra.append(definition.sytagmatic)
        if definition.level:
            extra.append(definition.level)
        if definition.areas:
            extra.append(", ".join(definition.areas))
        if definition.timeline:
            extra.append(definition.timeline)
        if extra:
            return "; ".join(extra)
        if parent_definition:
            return self.generate_definition(parent_definition.definition)
        return "<unknown definition>"

    def generate_examples(self, term: 'ResultTerm', limit):
        ordered = sorted(term.examples, key=lambda x: len(x))
        for i in range(min(limit, len(ordered))):
            yield ordered[i]

    def map_to_results(self, terms: Terms) -> List['ResultTerm']:
        if (not terms or not terms.terms): return []
        for term in terms.terms:
            yield self.map_to_result(term)

    def get_id(self, term:Term):
        return None if (not term or not term.id) else term.id
    def map_to_result(self, term: Term, parent: Term = None) -> 'ResultTerm':
        parent_id = self.get_id(parent)
        child_id = self.get_id(term)
        id = child_id if child_id else parent_id
        examples = list(self.pretify_elements(term.usages))
        definition = self.map_definition(term.definition, term.constraint)
        phrasems = [] if (not term.phraseme) else [it.text for it in term.phraseme]
        subterms = []
        if term.terms:
            for cur in term.terms:
                subterms.append(self.map_to_result(cur, term))
        return ResultTerm(id, definition=definition, examples=examples, subterms=subterms, phrasems=phrasems,
                          )

    def map_definition(self, definition: Def, constraint: str) -> 'ResultDefinition':
        definitions = [] if (not definition) else list(
            self.remove_separators(self.pretify_elements(definition.definitions), ";"))
        specification = None if (not definition) else definition.specification
        sytagmatic = None if (not definition) else definition.sytagmatic
        diasystem = None if (not definition) else definition.diasystem
        areas = [] if (not diasystem or not diasystem.areas) else list(self.pretify_elements(diasystem.areas))
        timeline = None if (not diasystem or not diasystem.timeline) else diasystem.timeline
        style = None if (not diasystem or not diasystem.style) else diasystem.style
        level = None if (not diasystem or not diasystem.level) else diasystem.level

        return ResultDefinition(
            definitions=definitions,
            constraint=constraint,
            timeline=timeline,
            specification=specification,
            areas=areas,
            level=level,
            style=style,
            sytagmatic=sytagmatic
        )

    def remove_separators(self, elements, separator):
        for element in elements:
            if element.strip() != separator.strip():
                yield element

    def pretify_elements(self, elements: list) -> list[str]:
        if not elements: return []
        for element in elements:
            if element.text:
                yield self.pretify(element.text)

    def pretify(self, text: str) -> str:
        # remove all whitespaces length of 2 or more
        removed_whitespaces = re.sub("\n", ' ', text)
        removed_double_lines = re.sub(' {2,}', ' ', removed_whitespaces)
        return removed_double_lines.strip()


@dataclasses.dataclass
class ResultDefinition:
    definitions: list[str]
    specification: str
    constraint: str  # in Verbindung mit 'in'
    sytagmatic: str  # (brennende Liebe)
    level: str
    areas: list[str]
    timeline: str
    style: str


@dataclasses.dataclass
class ResultTerm:
    id: str
    definition: ResultDefinition
    phrasems: list[str]  # (stehe auf etwas) = (gern haben)
    examples: list[str]
    subterms: list['ResultTerm']


if __name__ == "__main__":
    h = DWDSSearcher()
    # pprint.pprint(list(h.map_to_results(parse_dwds_result("aufkommen").terms)))
    # h.query("voreingenommen")
    h.query("vorkommen")
    # words = [
    # "häufig",
    # "Liebe",
    # "hallo",
    # "vorkommen",
    # "auf",
    # "aus",
    # "mit",
    # "inmitten",
    # "Mitte",
    # "geil",
    # "voreingenommen"
    # "drauf stehen",
    # ""
    # "zum Gluck" -> synonym zu instead of definition
    # ]
    # for word in words:
    #     pprint.pprint(parse_dwds_result(word))
    # pprint.pprint(list(h.map_to_results(parse_dwds_result("aufkommen").terms)))
