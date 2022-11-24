import numpy
import spacy
from pygismeteo import Gismeteo
import os
import json
import requests
import pymorphy2
import subprocess
import sys

from module_frame import Module_frame


class Module(Module_frame):
    def __init__(self, path_to_module):
        super().__init__()

        self.nlp = None
        self.morph = None
        self.gismeteo = None
        self.name = "weather"
        self.path_to_module = path_to_module

        self.default_config = {
            "name": "weather",
            "version": "1.0.0",
            "active": 1,
            "level": 2,
            "use_presets": "ru",

            "presets": {
                "ru": {
                    "spacy": "ru_core_news_lg",
                    "keywords_input": ["погода"]
                },
                "en": {
                    "spacy": "en_core_web_lg",
                    "keywords_input": ["weather"]
                }
            }

        }

    def exit(self):
        self.save_config()

    def launch(self, path_to_config: str = None) -> None:
        self.load_config(path_to_config)
        try:
            self.nlp = spacy.load(self.config["presets"][self.config["use_presets"]]["spacy"])
        except:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "ru_core_news_lg"])
            self.nlp = spacy.load(self.config["presets"][self.config["use_presets"]]["spacy"])

        self.gismeteo = Gismeteo()
        self.morph = pymorphy2.MorphAnalyzer()

    def main(self, values: dict = {}):
        try:
            if values.get("input"):
                output = []
                for i in values.get("input", []):
                    tomorrow, after_tomorrow = False, False
                    input = i.lower()
                    class_weather = False
                    for word in self.config["presets"][self.config["use_presets"]]["keywords_input"]:
                        if word in input:
                            class_weather = True
                            break

                    if class_weather:
                        doc = self.nlp(i)
                        city = None
                        for ent in doc.ents:
                            if (ent.label_ == 'LOC'):
                                city = ent.text
                                break

                        if not city:
                            url = 'http://ipinfo.io/json'
                            data = requests.get(url).json()
                            search_results = self.gismeteo.search.by_query(data["city"])
                        else:
                            search_results = self.gismeteo.search.by_query(self.morph.parse(city)[0].normal_form)

                        for word in self.config["presets"][self.config["use_presets"]]["keywords_tomorrow"]:
                            if word in input:
                                if len(word.split()) == 1:
                                    input_split = input.split()
                                    if word in input_split:
                                        tomorrow = True
                                        break
                                else:
                                    tomorrow = True
                                    break

                        for word in self.config["presets"][self.config["use_presets"]]["keywords_after_tomorrow"]:
                            if word in input:
                                if len(word.split()) == 1:
                                    input_split = input.split()
                                    if word in input_split:
                                        after_tomorrow = True
                                        break
                                else:
                                    after_tomorrow = True
                                    break

                        city_id = search_results[0].id
                        step24 = self.gismeteo.step24.by_id(city_id, days=3)
                        if tomorrow:
                            output.append("Завтра в городе {} температура {}°C и {}".format(search_results[0].name,
                                                                                            step24[
                                                                                                1].temperature.air.avg.c,
                                                                                            step24[1].description.full))
                        elif after_tomorrow:
                            output.append(
                                "После завтра в городе {} температура {}°C и {}".format(search_results[0].name,
                                                                                        step24[2].temperature.air.avg.c,
                                                                                        step24[2].description.full))
                        else:
                            output.append("В городе {} температура {}°C и {}".format(search_results[0].name,
                                                                                     step24[0].temperature.air.avg.c,
                                                                                     step24[0].description.full))
                    if values.get("output"):
                        values["output"].extend(output)
                    else:
                        values["output"] = output

            return values
        except Exception as e:
            if values.get("logger"):
                logger = values.get("logger").getChild('input_app.main')
                logger.exception(e)

            return values
        return values


if __name__ == '__main__':
    pf = Module(os.getcwd())
    pf.launch()
    values = {"input": "Какая завтра погода"}
    print(pf.main(values))
