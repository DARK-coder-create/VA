from loader import Loader
from module_frame import Module_frame

import time

import os
import sys
import inspect


class VoiceAssistant(Module_frame):
    def __init__(self):
        super().__init__()

        self.loader = None
        self.name = "voice_assistant"
        self.modules = []

        self.files_dict = {}

    def launch(self, path_to_config: str = None) -> None:
        self.load_config(path_to_config)

        if self.config.get("setswitchinterval"):
            sys.setswitchinterval(self.config.get("setswitchinterval"))

        self.update_files_dict()
        self.run_modules()
        self.sorting_modules()

        self.main()


    def update_files_dict(self):
        if not self.loader:
            self.loader = Loader()
            self.loader.launch()

        self.loader.create_datadirs()
        self.files_dict = self.loader.load_datadirs(self.loader.config.get("data_dirs", {}))

    def run_modules(self):
        self.modules = []
        for key in self.files_dict:
            for obj in self.files_dict[key]:
                if isinstance(obj, dict):
                    if obj.get("module"):
                        self.modules.append(obj["module"])
                        if VoiceAssistant.has_method(obj["module"], "launch"):
                            obj["module"].launch()
                        else:
                            obj["module"].load_config()
                            obj["module"].config["active"] = 0

    def sorting_modules(self, reverse:bool=False):
        self.modules = sorted(self.modules, key=lambda module: module.config.get("level", -1), reverse=reverse)

    @staticmethod
    def has_method(o, name):
        return callable(getattr(o, name, None))

    def exit(self):
        for module in self.modules:
            if VoiceAssistant.has_method(module, "exit"):
                module.exit()

    def run_commands(self, values):
        if values.get("exit"):
            self.run = False
        if values.get("reload"):
            self.run = False
            print(101)
            self.exit()
            self.launch()

    def main(self):
        self.run = True
        values = {}
        print(self.modules)
        while self.run:
            try:
                for module in self.modules:
                    values = module.main(values)

                self.run_commands(values)

                if self.config.get("delay_cycle"):
                    time.sleep(self.config["delay_cycle"])
            except Exception as e:
                print(e)
                self.run = False
        self.exit()




if __name__ == '__main__':
    pf = VoiceAssistant()
    pf.launch()