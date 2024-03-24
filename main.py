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
    link: str


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
            yield {
                "Title": result.title,
                # max 60 x 2
                "SubTitle": self.clean_subtitle(result.subtitle, 85),
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": [result.link]
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

    def transform(self, word, result: Result):
        if result.lemma and result.lemma.text:
            yield QueryResult(title=result.lemma.text, subtitle="", link=self.link(word))

        if not result.terms or not result.terms.terms: return

        for term in result.terms.terms:
            for result in self.generate_results(term):
                yield result

            # definitions = str(term.definition)
            # usages = term.usages
            #
            # for subterm in term.terms:
            #     subdefinitions = str(subterm.definition)
            #     subusages = subterm.usages
            #
            #     if not subusages:
            #         yield QueryResult(title=subdefinitions, subtitle='', link=self.link(word, subterm.id))
            #         continue
            #     for usage in subusages:
            #         yield QueryResult(title=subdefinitions, subtitle=usage.text, link=self.link(word, subterm.id))
            # if not usages:
            #     yield QueryResult(title=definitions, subtitle='', link=self.link(word, term.id))
            #     continue
            # for usage in usages:
            #     yield QueryResult(title=definitions, subtitle=usage.text, link=self.link(word, term.id))

    def generate_definition_and_examples(self, term: Term, parent_definition: Def):
        definition = self.generate_definition(term.definition, parent_definition)
        # examples = self.generate_examples(term.)

    def generate_definition(self, definition: Def, parent_defintion: Def):
        if not definition: return

    def generate_examples(self, ):
        pass

    def map_to_results(self, terms: Terms) -> List['ResultTerm']:
        for term in terms.terms:
            yield self.map_to_result(term)

    def map_to_result(self, term: Term) -> 'ResultTerm':
        id = term.id
        examples = list(self.pretify_elements(term.usages))
        definition = self.map_definition(term.definition, term.constraint, term.phraseme)
        subterms = []
        if term.terms:
            for term in term.terms:
                subterms.append(self.map_to_result(term))
        return ResultTerm(id, definition=definition, examples=examples, subterms=subterms)

    def map_definition(self, definition: Def, constraint: str, phrasems: list[Phrasem]) -> 'ResultDefinition':
        definitions = [] if (not definition) else list(self.remove_separators(self.pretify_elements(definition.definitions), ";"))
        phrasems = [] if (not phrasems) else [it.text for it in phrasems]
        sytagmatic = None if (not definition) else definition.sytagmatic
        specification = None if (not definition) else definition.specification
        diasystem = None if (not definition) else definition.diasystem
        areas = [] if (not diasystem or not diasystem.areas) else list(self.pretify_elements(diasystem.areas))
        timeline = None if (not diasystem or not diasystem.timeline) else diasystem.timeline
        style = None if (not diasystem or not diasystem.style) else diasystem.style
        level = None if (not diasystem or not diasystem.level) else diasystem.level

        return ResultDefinition(
            definitions=definitions,
            constraint=constraint,
            phrasems=phrasems,
            timeline=timeline,
            sytagmatic=sytagmatic,
            specification=specification,
            areas=areas,
            level=level,
            style=style,
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
    constraint: str
    phrasems: list[str]
    sytagmatic: str
    level: str
    areas: list[str]
    timeline: str
    style: str


@dataclasses.dataclass
class ResultTerm:
    id: str
    definition: ResultDefinition
    examples: list[str]
    subterms: list['ResultTerm']


if __name__ == "__main__":
    h = DWDSSearcher()
    # h.query("geil")
    terms = parse_dwds_result("geil")
    pprint.pprint(list(h.map_to_results(terms.terms)))
