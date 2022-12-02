from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.preprocessing.text import Tokenizer
from keras_preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from tensorflow.keras import layers
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.callbacks import CSVLogger

from tensorflow.keras.models import load_model

import json
import os
import numpy as np
import pickle


class CB_model:
    def __init__(self, path_to_module):
        self.path_to_module = path_to_module

        self.model = None

        self.config = None

        self.maxlen_x, self.maxlen_y = 0, 0
        self.train_x = None
        self.train_y = None
        self.tokenizer = None


    def get_base_config(self):
        return {
              "name": "model",
              "version": "1.0.0",

              "usage": {
                "datakeys": "data/datakeys/model.pickle",
                "model": "data/models/model.h5"
              },


              "learning": {
                "datakeys": "data/datakeys/model.pickle",
                "database": "data/database/model.txt",

                "filter": "''!\"#$%&\\'()*+,-./:;=?@[\\\\]^_`{|}~'",

                "batch_size": 32,
                "epochs": 100,
                "loss": "categorical_crossentropy",
                "optimizer": "rmsprop",
                "rmsprop_learning_rate": 0.01,
                "metrics": ["accuracy"],
                "save_csv_log": "data/log/model.csv",

                "start_tag": "<start>",
                "end_tag": "<end>",

                "save_model": "data/models/model.h5"
              }
        }

    def load_config(self, file_or_path=None):
        try:
            if isinstance(file_or_path, str):
                if file_or_path:
                    if os.path.isabs(file_or_path):
                        with open(os.path.join(file_or_path)) as f:
                            self.config = json.load(f)
                    else:
                        with open(os.path.join(self.path_to_module, file_or_path)) as f:
                            self.config = json.load(f)
                else:
                    with open(os.path.join(self.path_to_module, "data/config/model.config")) as f:
                        self.config = json.load(f)
            elif isinstance(file_or_path, dict):
                self.config = file_or_path
            else:
                self.config = self.get_base_config()
        except:
            self.config = self.get_base_config()

    def load_database_txt(self):
        tokenizer = Tokenizer(filters="", oov_token="<unknown>")
        maxlen_x, maxlen_y = 0, 0
        x, y = [], []
        vocab = set()

        with open(os.path.join(self.path_to_module, self.config["learning"]["database"]), encoding="utf-8") as file:
            for line in file:
                processed_line = line.translate(str.maketrans('', '', self.config["learning"]["filter"])).lower().split()

                if len(processed_line) > 1:
                    for word in processed_line[1:]:
                        vocab.add(word)

                    if processed_line[0] == "1":
                        x.append(processed_line[1:])
                        if len(processed_line[1:]) > maxlen_x:
                            maxlen_x = len(processed_line[1:])

                    elif processed_line[0] == "2":
                        y.append(processed_line[1:])
                        if len(processed_line[1:]) > maxlen_y:
                            maxlen_y = len(processed_line[1:])

        tokenizer.fit_on_texts(vocab)

        vocabularySize = len(vocab) + 2

        return x, y, tokenizer, vocabularySize, maxlen_x, maxlen_y

    def data_processing(self, x, y, tokenizer, vocabularySize, maxlen_x, maxlen_y):
        encoderForInput = tokenizer.texts_to_sequences(x)
        decoderForInput = tokenizer.texts_to_sequences(y)

        encoderForInput = pad_sequences(encoderForInput, maxlen=maxlen_x, padding='post', truncating='post')
        decoderForInput = pad_sequences(decoderForInput, maxlen=maxlen_y, padding='post', truncating='post')

        tokenizedAnswers = decoderForInput.tolist()

        for i in range(len(tokenizedAnswers)):
            tokenizedAnswers[i] = tokenizedAnswers[i][1:]  # избавляемся от тега &lt;START>

        paddedAnswers = pad_sequences(tokenizedAnswers, maxlen=maxlen_y, padding='post')

        oneHotAnswers = to_categorical(paddedAnswers, vocabularySize)  # переводим в one hot vector
        decoderForOutput = np.array(oneHotAnswers)

        return encoderForInput, decoderForInput, decoderForOutput


    def create_training_model(self, encoderForInput, decoderForInput, decoderForOutput, vocabularySize):
        encoderInputs = layers.Input(shape=(None,), name="EncoderForInput")
        # Эти данные проходят через слой Embedding (длина словаря, размерность)
        encoderEmbedding = layers.Embedding(vocabularySize, 200, mask_zero=True, name="Encoder_Embedding")(
            encoderInputs)
        # Затем выход с Embedding пойдёт в LSTM слой, на выходе у которого будет два вектора состояния - state_h , state_c
        # Вектора состояния - state_h , state_c зададутся в LSTM слое декодера в блоке ниже
        encoderOutputs, state_h, state_c = layers.LSTM(200, return_state=True, name="Encoder_LSTM")(encoderEmbedding)
        encoderStates = [state_h, state_c]

        decoderInputs = layers.Input(shape=(None,), name="DecoderForInput")  # размеры на входе сетки (здесь будет decoderForInput)

        # Эти данные проходят через слой Embedding (длина словаря, размерность)
        # mask_zero=True - игнорировать нулевые padding при передаче в LSTM. Предотвратит вывод ответа типа: "У меня все хорошо PAD PAD PAD PAD PAD PAD.."
        decoderEmbedding = layers.Embedding(vocabularySize, 200, mask_zero=True, name="Decoder_Embedding")(
            decoderInputs)
        # Затем выход с Embedding пойдёт в LSTM слой, которому передаются вектора состояния - state_h , state_c
        decoderLSTM = layers.LSTM(200, return_state=True, return_sequences=True, name="Decoder_LSTM")
        decoderOutputs, _, _ = decoderLSTM(decoderEmbedding, initial_state=encoderStates)
        # И от LSTM'а сигнал decoderOutputs пропускаем через полносвязный слой с софтмаксом на выходе

        decoderDense = layers.Dense(vocabularySize, activation='softmax')
        output = decoderDense(decoderOutputs)

        model = Model([encoderInputs, decoderInputs], output)
        if self.config["learning"]["optimizer"] == "rmsprop":
            optimizer = RMSprop(learning_rate=self.config["learning"]["rmsprop_learning_rate"])
        else:
            optimizer = self.config["learning"]["optimizer"]
        model.compile(optimizer=optimizer, loss=self.config["learning"]["loss"], metrics=self.config["learning"]["metrics"])

        model.summary()

        csv_logger = CSVLogger(self.config["learning"]["save_csv_log"], append=True, separator=';')

        model.fit([encoderForInput, decoderForInput], decoderForOutput, batch_size=self.config["learning"]["batch_size"], epochs=self.config["learning"]["epochs"],
                       callbacks=[csv_logger])

        return model

    def makeInferenceModels(self, model):
        # Определим модель кодера, на входе далее будут закодированные вопросы(encoderForInputs), на выходе состояния state_h, state_c
        #encoderModel = Model(encoderInputs, encoderStates)
        _, f, g = model.get_layer("Encoder_LSTM").output
        encoderStates = [f, g]
        encoderModel = Model(model.get_layer("EncoderForInput").input, encoderStates)
        decoderStateInput_h = layers.Input(shape=(200,),
                                    name='decoderStateInput_h')  # обозначим размерность для входного слоя с состоянием state_h
        decoderStateInput_c = layers.Input(shape=(200,),
                                    name='decoderStateInput_c')  # обозначим размерность для входного слоя с состоянием state_c
        decoderStatesInputs = [decoderStateInput_h,
                               decoderStateInput_c]  # возьмем оба inputs вместе и запишем в decoderStatesInputs
        # Берём ответы, прошедшие через эмбединг, вместе с состояниями и подаём LSTM cлою
        #model.get_layer("Encoder_LSTM").output Decoder_Embedding
        decoderOutputs, state_h, state_c = model.get_layer("Decoder_LSTM")(model.get_layer("Decoder_Embedding").output, initial_state=decoderStatesInputs)
        #decoderOutputs, state_h, state_c = decoderLSTM(decoderEmbedding, initial_state=decoderStatesInputs)
        decoderStates = [state_h, state_c]  # LSTM даст нам новые состояния
        decoderOutputs = model.get_layer("dense")(
            decoderOutputs)  # и ответы, которые мы пропустим через полносвязный слой с софтмаксом
        # Определим модель декодера, на входе далее будут раскодированные ответы (decoderForInputs) и состояния
        # на выходе предсказываемый ответ и новые состояния
        decoderModel = Model([model.get_layer("DecoderForInput").input] + decoderStatesInputs, [decoderOutputs] + decoderStates)

        return encoderModel, decoderModel

    def train_model(self):
        x, y, tokenizer, vocabularySize, maxlen_x, maxlen_y = self.load_database_txt()
        encoderForInput, decoderForInput, decoderForOutput = self.data_processing(x, y, tokenizer, vocabularySize, maxlen_x, maxlen_y)

        model = self.create_training_model(encoderForInput, decoderForInput, decoderForOutput, vocabularySize)

        model.save(os.path.join(self.path_to_module, self.config["learning"]["save_model"]))

        with open(os.path.join(self.path_to_module, self.config["learning"]["datakeys"]), 'wb') as handle:
            pickle.dump([maxlen_x, maxlen_y, tokenizer], handle, protocol=pickle.HIGHEST_PROTOCOL)


    def start(self, config):

        self.load_config(config)

        self.model = load_model(os.path.join(self.path_to_module, self.config["usage"]["model"]))

        with open(os.path.join(self.path_to_module, self.config["usage"]["datakeys"]), "rb") as file:
            self.maxlen_x, self.maxlen_y, self.tokenizer = pickle.load(file)

        self.encModel, self.decModel = self.makeInferenceModels(self.model)


    def strToTokens(self, sentence: str, tokenizer, maxlen_x):
        words = sentence.lower().split()
        tokensList = list()
        for word in words:
            tokensList.append(tokenizer.word_index.get(word, 1))

        return pad_sequences([tokensList], maxlen=maxlen_x, padding='post')

    def get_answer(self, answer, tokenizer, maxlen_x, maxlen_y,
                   encModel, decModel):
        if answer:
            statesValues = encModel.predict(self.strToTokens(answer, tokenizer, maxlen_x))
            emptyTargetSeq = np.zeros((1, 1))
            emptyTargetSeq[0, 0] = tokenizer.word_index['<start>']

            stopCondition = False
            decodedTranslation = ''
            while not stopCondition:
                decOutputs, h, c = decModel.predict([emptyTargetSeq] + statesValues)

                sampledWordIndex = np.argmax(decOutputs[0, 0,:]).tolist()

                sampledWord = None  # создаем переменную, в которую положим слово, преобразованное на естественный язык
                for word, index in tokenizer.word_index.items():
                    if sampledWordIndex == index:
                        sampledWord = word  # выбранное слово фиксируем в переменную sampledWord

                # Если выбранным словом оказывается 'end' либо если сгенерированный ответ превышает заданную максимальную длину ответа
                if sampledWord == self.config["learning"]["end_tag"] or len(decodedTranslation.split()) > maxlen_y:
                    stopCondition = True
                else:
                    decodedTranslation += " " + sampledWord

                emptyTargetSeq = np.zeros((1, 1))  # создаем пустой массив
                emptyTargetSeq[0, 0] = sampledWordIndex  # заносим туда индекс выбранного слова
                statesValues = [h, c]  # и состояния, обновленные декодером
                # и продолжаем цикл с обновленными параметрами

            return decodedTranslation
        return None




if __name__ == '__main__':
    pf = CB_model("/data/modules/chatbot")

    #pf.start()
    pf.train_model()
