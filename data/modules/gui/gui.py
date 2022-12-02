import os

import speech_recognition as sr

from PyQt5.QtWidgets import QApplication, QMainWindow, qApp, QPushButton, QWidget, QGridLayout, QLabel, QListWidgetItem, \
    QGraphicsDropShadowEffect
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from threading import Thread


class CommaWrapableQLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(CommaWrapableQLabel, self).__init__(*args, **kwargs)

    def setWordWrapAtAnychar(self, char):
        newtext = self.text().replace(char, f"{char}\u200b")
        self.setText(newtext)
        self.setWordWrap(True)


class Window(QMainWindow):
    update_text = pyqtSignal(str, int)

    def __init__(self, path_to_module, settings):
        super().__init__()

        if settings is None:
            settings = {}

        self.settings = settings
        self.path_to_module = path_to_module

        self.manager_list = []

        self.run = True

        self.launch()

    def launch(self):
        if self.settings.get("path"):
            uic.loadUi(os.path.join(self.path_to_module, self.settings.get("path")), self)

        if self.settings.get("title"):
            self.setWindowTitle(self.settings.get("title"))

        if self.settings.get("size") and len(self.settings.get("size", [])) == 2:
            self.resize(self.settings.get("size")[0], self.settings.get("size")[1])

        if self.settings.get("speed_step_chat"):
            self.chat.verticalScrollBar().setSingleStep(self.settings.get("speed_step_chat"))

        self.send.clicked.connect(self.send_text)
        self.micro.clicked.connect(self.clicked_micro)
        self.input_text.returnPressed.connect(self.send_text)

        self.update_text.connect(self.add_text_to_chat)

        self.active_micro = []
        self.active_micro_bool = False

    def closeEvent(self, event):
        self.run = False

    def listen_micro(self, index):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source)

        try:
            if self.active_micro[index]:
                task = r.recognize_google(audio, language="ru-RU").lower()
                self.update_text.emit(task, 0)
                self.active_micro = []
                self.active_micro_bool = False
                self.micro.setStyleSheet("background-color : rgba(0, 0, 0, 0); font-size:18pt")
        except Exception as e:
            self.active_micro_bool = False
            self.micro.setStyleSheet("background-color : rgba(0, 0, 0, 0); font-size:18pt")
            self.update_text.emit("Ошибка записи аудио", 0)

    def clicked_micro(self):
        self.active_micro_bool = not self.active_micro_bool
        if len(self.active_micro) > 0:
            self.active_micro[-1] = False

        if self.active_micro_bool:
            self.active_micro.append(self.active_micro_bool)
            self.micro.setStyleSheet("background-color : blue; font-size:18pt")
            pf = Thread(target=self.listen_micro, args=(len(self.active_micro) - 1,), daemon=True)
            pf.start()
        else:
            self.micro.setStyleSheet("background-color : rgba(0, 0, 0, 0); font-size:18pt")

    def add_text_to_chat(self, text, who: bool = 0):
        if not who:
            self.manager_list.append(text)
        item = QListWidgetItem()
        # I create a custom widget*
        widget = CommaWrapableQLabel(text)
        # I set the Size from the Item to the same of the widget*

        if not who:
            widget.setStyleSheet(
                "background-color:white;padding:10px;margin:10px;border:1px solid black; border-radius:15px; font: 10pt 'MS Shell Dlg 2';")

        if who:
            widget.setStyleSheet(
                "background-color:rgb(179, 228, 239);padding:10px;margin:10px;border:1px solid black; border-radius:15px; font: 10pt 'MS Shell Dlg 2';")

        widget.setFixedWidth(360)
        widget.setWordWrap(True)
        widget.setScaledContents(True)
        widget.setWordWrapAtAnychar(" ")

        widget.adjustSize()
        item.setSizeHint(widget.size())

        shadow = QGraphicsDropShadowEffect()

        # setting blur radius
        shadow.setBlurRadius(15)

        # adding shadow to the label
        widget.setGraphicsEffect(shadow)
        # I add it to the list*
        self.chat.addItem(item)

        self.chat.setItemWidget(item, widget)

        self.chat.scrollToItem(item)

    def send_text(self):
        if len(self.input_text.text()) > 0:
            self.add_text_to_chat(self.input_text.text())
        self.input_text.setText("")
