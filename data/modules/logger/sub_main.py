import logging
import os
import json
import sys

from module_frame import Module_frame

#class <Logger>
class Module(Module_frame):
    def __init__(self, path_to_module):
        super().__init__()
        self.name = "logger"
        self.path_to_module = path_to_module

        self.default_config = {
            "name": "logger",
            "version": "1.0.0",

            "active": 1,

            "use_logger": 1,

            "level": -1,

            "logging": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "level": 10,
                "file_name": "logger_test",
                "path_dir_save": "log/",
                "file_extension": "log"

            },

            "data_input": ["status", "config"],

            "output": ["output", "logger"]
        }

    def launch(self, path_to_config: str = None) -> None:
        self.load_config(path_to_config)
        self.set_logger()

    def set_logger(self):
        if self.config:
            if not self.config.get("logging", {}).get("file_name"):
                file_path_name = os.path.join(self.path_to_module, self.config.get("logging", {}).get("path_dir_save", "log")) + "logger" + \
                                                                  "_" + str(len(os.listdir(os.path.join(self.path_to_module,
                                                                                                        self.config.get("logging", {}).get("path_dir_save", "log")))) + 1) + \
                                 "." + self.config.get("logging", {}).get("file_extension", "log")
            else:
                file_path_name = os.path.join(self.path_to_module, self.config.get("logging", {}).get("path_dir_save", "log")) + self.config.get("logging", {}).get("file_name") + \
                                 "." + self.config.get("logging", {}).get("file_extension", "log")
            handlers = []
            if self.config.get("print_to_console", 1):
                handlers.append(logging.StreamHandler())
            if self.config.get("print_to_file", 1):
                handlers.append(logging.FileHandler(file_path_name))

            logging.basicConfig(format=self.config["logging"]["format"],
                                level=self.config["logging"]["level"],
                                handlers=handlers)

    def main(self, values=None):
        if values is None:
            values = {}
        try:
            if not self.config.get("use_logger"):
                if "status" in self.config.get("data_input"):
                    if values.get("status"):
                        for msg in values.get("status"):
                            self.write_log_msg(msg)
            elif "config" in self.config.get("data_input"):
                if values.get("status"):
                    for msg in values.get("status"):
                        self.write_log_msg(msg)

        except Exception as e:
            self.write_log_msg(["Logger", logging.CRITICAL, e])


        values.pop("status", 0)
        values["logger"] = logging.getLogger()

        return values

    def write_log_msg(self, msg):
        logger = logging.getLogger(msg[0])
        if msg[1] == 10:
            logger.debug(" - ".join(msg[2:]))
        elif msg[1] == 20:
            logger.info(" - ".join(msg[2:]))
        elif msg[1] == 30:
            logger.warning(" - ".join(msg[2:]))
        elif msg[1] == 40:
            logger.error(" - ".join(msg[2:]))
        elif msg[1] == 50:
            logger.critical(" - ".join(msg[2:]))


if __name__ == '__main__':
    pf = Module("")
    pf.launch()
    pf.write_log_msg(["Loader.get_data_dir", logging.DEBUG, "path", "download start date of the folder"])
    pf.write_log_msg(["Loader.get_data_dir", logging.INFO, "path", "download start date of the folder"])
    pf.write_log_msg(["Loader.get_data_dir", logging.ERROR, "path", "download start date of the folder"])
    pf.write_log_msg(["Loader.get_data_dir", logging.CRITICAL, "path", "download start date of the folder"])
