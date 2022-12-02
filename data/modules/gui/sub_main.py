import time
import sys

from module_frame import Module_frame
from multiprocessing import Process, Manager

import speech_recognition as sr

from data.modules.gui.gui import Window

from PyQt5.QtWidgets import QApplication

from threading import Thread


class Module(Module_frame):
    def __init__(self, path_to_module):
        super().__init__()
        self.name = "gui_app"

        self.path_to_module = path_to_module

        self.window = None

        self.default_config = {
            "name": "gui_app",
            "version": "2.0.0",
            "active": 1,
            "level": 1,

            "ui_file": {
                "path": "data/app.ui",
                "title": "Голосовой Ассистент. Интерфейс",
                "size": [640, 960]
            }
        }

    def launch(self, path_to_config: str = None) -> None:
        self.window = None
        self.load_config(path_to_config)

        pf = Thread(target=self.create, args=(), name="gui")
        pf.start()

    def exit(self, path_to_config: str = None) -> None:
        self.save_config(path_to_config)

    def main(self, values=None):
        if values is None:
            values = {}
        try:
            if values.get("input"):
                values["input"].clear()
            if self.window:
                if len(self.window.manager_list) > 0:
                    if values.get("logger"):
                        values.get("logger").getChild(f"{self.name}.main").info(f"get input {self.window.manager_list}")
                    values["input"] = self.window.manager_list.copy()
                    if values.get("input"):
                        if values.get("logger"):
                            logger = values.get("logger").getChild(f'{self.name}.main')
                            logger.info(f"send input {values.get('input')}")
                    self.window.manager_list = []

                if len(values.get("output", [])) > 0:
                    if values.get("logger"):
                        values.get("logger").getChild(f"{self.name}.main").info(
                            f"print output {values.get('output', [])}")
                    for i in range(len(values["output"])):
                        self.window.update_text.emit(values["output"][i], 1)
                    values["output"] = []

                if not self.window.run:
                    if values.get("logger"):
                        values.get("logger").getChild(f"{self.name}.main").info("exit")
                    values["exit"] = True
        except Exception as e:
            if values.get("logger"):
                logger = values.get("logger").getChild('input_app.main')
                logger.exception(e)

        return values

    def create(self):
        app = QApplication(sys.argv)
        self.window = Window(self.path_to_module, self.config.get("ui_file"))
        self.window.show()
        app.exec_()


if __name__ == '__main__':
    dd = Module("")
    dd.launch()
