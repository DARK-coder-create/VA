import os
import importlib.util
import logging

import colorama

from module_frame import Module_frame


class CustomFormatter(logging.Formatter):
    def __init__(self, formatt):
        super().__init__()
        self.formatt = formatt
        self.FORMATS = {
            logging.DEBUG: "\33[1;37m" + formatt + colorama.Fore.RESET,
            logging.INFO: colorama.Fore.GREEN + formatt + colorama.Fore.RESET,
            logging.WARNING: colorama.Fore.YELLOW + formatt + colorama.Fore.RESET,
            logging.ERROR: colorama.Fore.LIGHTRED_EX + formatt + colorama.Fore.RESET,
            logging.CRITICAL: colorama.Fore.RED + formatt + colorama.Fore.RESET,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Loader(Module_frame):
    def __init__(self):
        super().__init__()

        self.name = "loader"

        self.default_config = {
            "name": "loader",
            "version": "2.0.0",

            "description": "pass",

            "logging": {
                "use": True,
                "print_to_console": 1,
                "print_to_file": 1,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "level": 10,
                "file_name": "loader",
                "file_extension": "log",
                "path_dir_save": ""
            },

            "data_dirs": {
                "use_dirs": ["main_dir"],
                "main_dir": {
                    "path": "data",
                    "use_files": ["modules", "configs", "loggers", "dirs"],
                    "files": {
                        "modules": {
                            "files_extension": ["py", "pyw"],
                            "selecting_specific_files": ["main", "sub_main"],
                            "exception_files": []
                        },
                        "configs": {
                            "files_extension": ["config"],
                            "selecting_specific_files": [],
                            "exception_files": []
                        },
                        "loggers": {
                            "files_extension": [".log"],
                            "selecting_specific_files": [],
                            "exception_files": []
                        },
                        "dirs": {
                            "files_extension": [],
                            "selecting_specific_files": [],
                            "exception_files": ["__pycache__"]
                        }
                    }
                }
            }
        }

        self.logger = None

    def launch(self, path_to_config: str = None) -> None:
        """
        The function that is needed to run the initial class settings

        Функция, которая необходима для запуска первоначальных настроек класса
        """
        self.logger = None

        self.load_config(path_to_config)
        self.set_logger()

        if self.logger:
            self.logger.info("launch")

        self.create_datadirs()

    def set_logger(self):
        if self.config and self.config.get("logging", {}).get("use"):
            if not self.config.get("logging", {}).get("file_name"):
                file_path_name = os.path.join(self.path_to_module, self.config.get("logging", {}).get("path_dir_save", "")) + "logger" + \
                                                                  "_" + str(len(os.listdir(os.path.join(self.path_to_module,
                                                                                                        self.config.get("logging", {}).get("path_dir_save", "log")))) + 1) + \
                                 "." + self.config.get("logging", {}).get("file_extension", "log")
            else:
                file_path_name = os.path.join(self.path_to_module, self.config.get("logging", {}).get("path_dir_save", "")) + self.config.get("logging", {}).get("file_name") + \
                                 "." + self.config.get("logging", {}).get("file_extension", "log")

            self.logger = logging.getLogger(self.name)
            formatter = logging.Formatter(self.config["logging"]["format"])

            if self.config.get("print_to_file", 1):
                fileHandler = logging.FileHandler(file_path_name)
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)

            if self.config.get("print_to_console", 1):
                streamHandler = logging.StreamHandler()
                #streamHandler.setFormatter(formatter)
                streamHandler.setFormatter(CustomFormatter(self.config["logging"]["format"]))
                self.logger.addHandler(streamHandler)

            self.logger.setLevel(self.config["logging"]["level"])


            """logging.basicConfig(format=self.config["logging"]["format"],
                                level=self.config["logging"]["level"],
                                handlers=handlers)"""

            #self.logger = logging.getLogger(self.name.capitalize())

    def load_datadirs(self, settings=None):
        values = {}

        if settings is None:
            settings = {}

        dirs = settings.get("use_dirs", [])
        for dir in dirs:
            settings_files = {}
            if self.logger:
                self.logger.info(f"load datadir {dir} {self.get_datadir(settings.get(dir).get('path'))}")
            values = self.update_dict(values, self.get_datadir(settings.get(dir).get("path"), settings.get(dir)))

        return values

    @staticmethod
    def update_dict(d1, d2):
        """
        A function whose essence is to combine two dictionaries in the format of lists, where d1 is a dictionary to which d2 is added

        Функция, суть которой объединить два словаря в формате списков, где d1 это словарь к которому добавляют d2
        """
        for key in d1:
            if d2.get(key):
                d1[key].extend(d2.get(key))
        for key in d2:
            if not d1.get(key):
                d1[key] = d2[key]

        return d1

    def create_datadirs(self) -> None:
        """

        Функция, которая
        """
        for dirs in self.config.get("data_dirs", {}).get("use_dirs", []):
            if not os.path.exists(self.config["data_dirs"][dirs]["path"]):
                os.mkdir(self.config["data_dirs"][dirs]["path"])

                if self.logger:
                    self.logger.info(f'create data dir {self.config["data_dirs"][dirs]["path"]}')

    def get_datadir(self, path, settings=None):
        if self.logger:
            self.logger.info(f"get datadir - {path}")
        values = {}
        if settings is None:
            settings = {}

        settings_files = {}
        for type_file in settings.get("use_files", []):
            settings_files[type_file] = settings.get("files").get(type_file, {})

        dirs = self.get_dirs_from_datadir(path, settings_files.get("dirs", {}))

        values["dirs"] = dirs

        for dir in dirs:
            val = self.get_files_from_dir(dir, settings_files)
            values = self.update_dict(values, val)

        return values

    def get_dirs_from_datadir(self, path: str = os.getcwd(), settings=None):
        if settings is None:
            settings = {}
        dirs = []
        for path_dir, _, _ in os.walk(path):
            if len(settings.get("dirs", {}).get("selecting_specific_files", [])) > 0:
                if os.path.basename(path_dir) in settings["dirs"]["selecting_specific_files"]:
                    dirs.append(path_dir)
            elif len(settings.get("dirs", {}).get("exception_files", [])) > 0:
                if not os.path.basename(path_dir) in settings["dirs"]["exception_files"]:
                    dirs.append(path_dir)
            else:
                dirs.append(path_dir)

        if self.logger:
            self.logger.debug(f"received dir from date_dir - {dirs}")
            self.logger.info(f"received dir from date_dir - {len(dirs)}")

        return dirs

    def get_files_from_dir(self, path: str = os.getcwd(), settings=None):
        if settings is None:
            settings = {}
        values = {}
        for type_file in settings:
            if type_file != "dirs":
                values[type_file] = []

        files = [file for file in os.listdir(path) if not os.path.isdir(os.path.join(path, file))]

        for file in files:
            for type_file in values:
                use_file = False
                if len(settings.get(type_file, {}).get("files_extension", [])) > 0:
                    if os.path.splitext(file)[-1][1:] in settings[type_file]["files_extension"]:
                        use_file = True

                if len(settings.get(type_file, {}).get("selecting_specific_files", [])) > 0:
                    if not os.path.splitext(file)[0] in settings[type_file]["selecting_specific_files"]:
                        use_file = False

                if len(settings.get(type_file, {}).get("exception_files", [])) > 0:
                    if os.path.splitext(file)[0] in settings[type_file]["exception_files"]:
                        use_file = False

                if use_file:
                    file_dict = {"name": os.path.splitext(file)[0],
                                 "path": os.path.join(path, file),
                                 "file_extension": os.path.splitext(file)[-1][1:]}

                    if settings.get(type_file, {}).get("is_python_module", False):
                        try:
                            spec = importlib.util.spec_from_file_location("module", file_dict["path"])
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            class_module = module.Module(path)
                            file_dict["module"] = class_module
                        except: pass

                    if self.logger:
                        self.logger.debug(f"get file {file_dict}")

                    values[type_file].append(file_dict)

        return values


if __name__ == '__main__':
    pf = Loader()
    pf.launch()
    pf.create_datadirs()
    val = pf.load_datadirs(pf.config["data_dirs"])
    for i in range(len(val["modules"])):
        print(val["modules"][i])
