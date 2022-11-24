import json
import os


class Module_frame:
    def __init__(self):
        """
        The class, which is the framework for all modules, includes: loading, saving, getting the configuration

        Класс, который является каркасом для всех модулей, включает в себя: загрузку, сохранение, получение конфигурации
        """
        self.name = None
        self.config = {}
        self.default_config = None

        self.path_to_module = ""

    def load_config(self, file_or_path: (dict | str) = None) -> dict:
        """
        A function that loads the module configuration in json format.
        Accepts file, path, or None.

        Функция, которая загружает конфигурацию модуля в формате json.
        Принимает файл, путь или None.
        """
        try:
            use_path = os.path.join(self.path_to_module, f"{self.name if self.name else 'unknown_module'}.config")
            if isinstance(file_or_path, str):
                with open(file_or_path, encoding="utf-8") as file:
                    self.config = json.load(file)
            elif isinstance(file_or_path, dict):
                self.config = file_or_path.copy()
            else:
                with open(use_path, encoding='utf-8') as file:
                    self.config = json.load(file)
            return {"ok": "Successful configuration load"}
        except Exception as e:
            print(self.name)
            print("FF", e)
            self.config = self.get_default_config()
            self.save_config()
            return {"error": e}

    def save_config(self, path: str = None) -> dict:
        """
        A function that loads the module configuration in json format.
        Accepts file, path, or None.

        Функция, которая сохраняет текущую конфигурацию модуля в формате json.
        Принимает путь или None.
        """
        try:
            use_path = os.path.join(self.path_to_module, f"{self.name if self.name else 'unknown_module'}.config")
            if isinstance(path, str):
                use_path = path

            with open(use_path, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, ensure_ascii=False, indent=4)

            return {"ok": "Successful configuration save"}
        except Exception as e:
            return {"error": e}

    def get_default_config(self) -> dict:
        """
        A function that returns the basic (backup configuration of the module)

        Функция, которая возвращает базовую(резервную конфигурацию модуля)
        """

        if self.default_config:
            return self.default_config
        else:
            return {
                "name": "unknown_module",
                "version": "unknown_version",
                "active": 0,
                "level": -1,
                "description": "nothing"
            }

    def __repr__(self) -> str:
        """
        A function that returns a short description of the module, namely: Class name, Module name,
        Activity, version, description

        Функция, которая возвращает краткое описания модуля, а именно: Имя класса, имя модуля,
        активность, версию, описание
        """

        return f"<{self.name if self.name else 'unknown_module'}> " \
               f"(name: {self.config.get('name', 'unknown_module')}, " \
               f"active: {self.config.get('active', 0)}, " \
               f"level: {self.config.get('level', -1)}, " \
               f"description: {self.config.get('description', 'empty')})"
