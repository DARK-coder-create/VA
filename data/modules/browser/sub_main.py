import asyncio
import websockets
import json
import pymorphy2
from data.modules.browser.extractor import NumberExtractor
import threading
import time

from module_frame import Module_frame


class Module(Module_frame):
    def __init__(self, path_to_module):
        super().__init__()

        self.name = "browser"

        self.path_to_module = path_to_module
        self.morph = pymorphy2.MorphAnalyzer()

        self.command = []

    def launch(self, path_to_config: str = None) -> None:
        self.load_config()
        t = threading.Thread(target=self.webserver_run)
        t.start()

    def exit(self):
        self.save_config()

    def webserver_run(self):
        asyncio.run(self.server_main())

    async def handler(self, websocket):
        while True:
            await asyncio.sleep(1)
            if len(self.command) > 0:
                await websocket.send(json.dumps(self.command[0]))
                del self.command[0]

    async def server_main(self):
        async with websockets.serve(self.handler, "localhost", 9090):
            await asyncio.Future()


    def main(self, values:dict={}):
        try:
            if values.get("input"):
                for inputе in values.get("input"):
                    input_str = NumberExtractor().replace_groups(inputе)
                    new_input = []
                    input_browser = inputе.split()

                    for i in input_str.split():
                        new_input.append(self.morph.parse(i)[0].normal_form)

                    open_tab = 0
                    close_tab = 0
                    switch_tab = 0
                    for word in new_input:
                        if word in self.config.get("presets").get("ru").get("open_tab"):
                            open_tab += 1
                        if word in self.config.get("presets").get("ru").get("close_tab"):
                            close_tab += 1
                        if word in self.config.get("presets").get("ru").get("switch_tab"):
                            switch_tab += 1
                    if max(open_tab, close_tab, switch_tab) > 0:
                        if open_tab == max(open_tab, close_tab, switch_tab):
                            for i in self.config.get("presets").get("ru").get("open_tab"):
                                try:
                                    input_browser[new_input.index(i)] = ""
                                except Exception as e:
                                    pass
                            if len(" ".join(input_browser)) > 0:
                                val = {"command": "open_tab", "url": "", "text": " ".join(input_browser)}
                            else:
                                val = {"command": "open_tab", "url": "chrome://newtab/", "text": ""}
                            self.command.append(val)

                        elif close_tab == max(open_tab, close_tab, switch_tab):
                            if_int = 0
                            for i in self.config.get("presets").get("ru").get("close_tab"):
                                try:
                                    input_browser[new_input.index(i)] = ""
                                except Exception as e:
                                    pass

                            for word in input_browser:
                                if word.isdigit():
                                    if_int = int(word)
                            val = {"command": "remove_tab", "number_tab": if_int}
                            self.command.append(val)

                        elif switch_tab == max(open_tab, close_tab, switch_tab):
                            if_int = 0
                            for i in self.keyword["switch_tab"]:
                                try:
                                    input_browser[new_input.index(i)] = ""
                                except Exception as e:
                                    pass

                            for word in input_browser:
                                if word.isdigit():
                                    if_int = int(word)
                            val = {"command": "switch_tab", "number_tab": if_int}
                            self.command.append(val)
        except Exception as e:
            if values.get("logger"):
                logger = values.get("logger").getChild('input_app.main')
                logger.exception(e)
            return values
        return values


if __name__ == "__main__":
    pf = Module("")
    pf.launch()

    while True:
        values = {
            "input": [input(">>")]
        }
        pf.main(values)