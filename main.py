# -*- coding: utf-8 -*-
import dataclasses
import os
import pprint
import re
import sys
import time

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from dwds_model import Result, Term
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
            f.write("queried: "+query+"\n")
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
        # remove all whitespaces length of 2 or more
        removed_whitespaces = re.sub("\n", ' ', title)
        removed_double_lines = re.sub(' {2,}', ' ', removed_whitespaces)
        return self.soft_break_after(removed_double_lines, break_index).strip()

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
                "SubTitle": "Press enter to open Flow the plugin's repo in GitHub\n"*10,
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

        if not result.terms: return

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
    def generate_definitions(self, term: Term):
        pass

if __name__ == "__main__":
    # h = DWDSSearcher()
    # h.query("geil")
    terms = parse_dwds_result("geil")
    pprint.pprint(terms)
