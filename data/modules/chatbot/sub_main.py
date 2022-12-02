import os
import json
from data.modules.chatbot.model import CB_model
from module_frame import Module_frame


class Module(Module_frame):
    def __init__(self, path_to_module):
        super().__init__()
        self.path_to_module = path_to_module

        self.name = "chatbot"

        self.model = None

        self.default_config = {
            "name": "chatbot",
            "version": "1.0.0",
            "active": 1,
            "level": 2,

            "use_presets": "default",

            "presets": {
                "default": "data/config/default.json"
            },
        }


    def launch(self):
        self.load_config()
        self.model = CB_model(self.path_to_module)
        self.model.start(self.config["presets"][self.config["use_presets"]])

    def main(self, values:dict={}):
        try:
            if values.get("input"):
                if values.get("logger"):
                    logger = values.get("logger").getChild(f'{self.name}.main')
                    logger.info(f"get input {values.get('input')}")

            if self.model:
                for text in values.get("input", []):
                    answer = self.model.get_answer(text, self.model.tokenizer, self.model.maxlen_x,
                                              self.model.maxlen_y, self.model.encModel, self.model.decModel)

                    if answer:
                        if values.get("output"):
                            values["output"].append(answer)
                        else:
                            values["output"] = [answer]

                    if values.get("output"):
                        if values.get("logger"):
                            logger = values.get("logger").getChild(f'{self.name}.main')
                            logger.info(f"send output {values.get('output')}")
        except Exception as e:
            if values.get("logger"):
                logger = values.get("logger").getChild('input_app.main')
                logger.exception(e)

            values["status"].append(e)

        return values


if __name__ == '__main__':
    pf = Module(os.getcwd())
    pf.launch()
    pf.model.train_model()