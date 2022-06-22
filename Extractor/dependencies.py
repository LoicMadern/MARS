import os
import json


def extract(system):
    dependencies = []
    os.system('ruby ManifestParser/scanner.rb ' + system + ' > raw_dependencies.json')
    with open("raw_dependencies.json") as raw_dependencies:
        data = json.load(raw_dependencies)
        for node in data:
            if node["platform"] == "maven" and node["dependencies"]:
                for item in node["dependencies"]:
                    dependencies.append(item["name"])
    os.remove("raw_dependencies.json")
    return dependencies
