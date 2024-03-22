# -*- coding: utf-8 -*-
import dataclasses
import os
import sys
import time

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from dwds_model import Result
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
            time.sleep(1)

        result = parse_dwds_result(query)
        for result in self.transform(query, result):
            yield {
                "Title": result.title,
                "SubTitle": result.subtitle,
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": [result.link]
                }
            }

    def context_menu(self, data):
        return [
            {
                "Title": "Hello World Python's Context menu",
                "SubTitle": "Press enter to open Flow the plugin's repo in GitHub",
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": ["https://github.com/Flow-Launcher/Flow.Launcher.Plugin.HelloWorldPython"]
                }
            }
        ]

    def open_url(self, url):
        webbrowser.open(url)

    def link(self, word, id = None):
        return "https://www.dwds.de/wb/"+word+"#"+("" if not id else id)

    def transform(self, word, result: Result):
        if result.lemma and result.lemma.text:
            yield QueryResult(title=result.lemma.text, subtitle="", link=self.link(word))
        if not result.terms or not result.terms.terms:
            return

        for term in result.terms.terms:
            definitions = str(term.definition.definitions)
            usages = term.usages
            if not usages:
                yield QueryResult(title=definitions, subtitle='', link=self.link(word, term.id))
            for usage in usages:
                yield QueryResult(title=definitions, subtitle=usage.text, link=self.link(word, term.id))


if __name__ == "__main__":
    h = DWDSSearcher()
    # terms = parse_dwds_terms("häufig")
    # pprint.pprint(terms)
    # pprint.pprint(list(h.transform(terms)))
