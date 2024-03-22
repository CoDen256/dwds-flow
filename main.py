# -*- coding: utf-8 -*-
import pprint
import sys, os
import time

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from flowlauncher import FlowLauncher
from dwds import parse_dwds_terms
import webbrowser



class DWDSSearcher(FlowLauncher):

    def query(self, param):
        return list(self.generate_results(param))

    def generate_results(self, query):
        if len(query) <= 1: return []
        if len(query) <= 4:
            time.sleep(1)

        terms = parse_dwds_terms(query)
        for (title, subtitle) in self.transform(terms):
            yield {
                "Title": title,
                "SubTitle": subtitle,
                "IcoPath": "Images/app.png",
                "JsonRPCAction": {
                    "method": "open_url",
                    "parameters": ["https://www.dwds.de/wb/"+query]
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

    def transform(self, terms):
        for term in terms:
            if not term.examples and not term.subterms:
                yield term.definition, ""
            for example in term.examples:
                yield term.definition, example
            for subterm in self.transform(term.subterms):
                yield term.definition + "|" + subterm[0], subterm[1]


if __name__ == "__main__":
    h = DWDSSearcher()
    # terms = parse_dwds_terms("häufig")
    # pprint.pprint(terms)
    # pprint.pprint(list(h.transform(terms)))
