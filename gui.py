import sys

import qt_async_threads
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QInputDialog,
                             QLabel, QVBoxLayout, QWidget, QDialog, QListWidget, QDialogButtonBox, QListView)
import PyQt5.QtCore as QtCore
from enum import Enum


# callback = function(id:int, payload)
class CallType(Enum):
    LOGIN = 1
    SEARCH = 2
    LOAD_BOOKS = 3
    DOWNLOAD = 4


class ListSelectDialog(QDialog):
    """Диалог выбора элемента из списка"""

    def __init__(self, items: list, title: str):
        super().__init__()
        self.init_ui(items, title)

    def init_ui(self, items: list[str], title: str):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.lst_view = QListWidget(self)
        self.lst_view.addItems(items)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.lst_view)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

        # "Найдены cookies c SID"
        self.setWindowTitle(title)

        self.resize(300, 300)

    def get_data(self) -> tuple[int, str]:
        return self.lst_view.currentRow(), self.lst_view.item(self.lst_view.currentRow()).text()


class MainWindow(QMainWindow):
    def __init__(self, callback: callable):
        super().__init__()
        self.sid = ""
        self.runner = qt_async_threads.QtAsyncRunner()
        self.callback = callback

        self.call_worker = self.runner.to_sync(self.async_call_worker)

        self.setWindowTitle("Шаг 1. Получить SID")
        self.setGeometry(300, 300, 400, 200)
        self.setFixedHeight(200)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.button_login = QPushButton("Вход в ЛК Litres", self)
        self.button_search = QPushButton("*Искать в cookies*", self)
        self.button_search.setEnabled(False)

        self.button_input = QPushButton("Ввести вручную", self)

        self.sid_label = QLabel(self)
        self.sid_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.sid_label.setStyleSheet("border-radius: 25px;border: 1px solid black;")

        self.button_run = QPushButton("Старт", self)
        self.button_run.setEnabled(False)

        layout.addWidget(self.button_login)
        layout.addWidget(self.button_search)
        layout.addWidget(self.button_input)
        layout.addWidget(self.sid_label)
        layout.addWidget(self.button_run)
        layout.addStretch()

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.set_sid("")

        self.button_login.clicked.connect(self.try_login)
        self.button_search.clicked.connect(self.try_search)
        self.button_input.clicked.connect(self.input_sid)
        self.button_run.clicked.connect(self.run_loading)

    def set_sid(self, sid_value: str):
        if sid_value:
            self.sid_label.setText(sid_value)
            self.sid = sid_value
            self.sid_label.setStyleSheet("background-color: green;")
        else:
            self.sid_label.setText("No SID")
            self.sid_label.setStyleSheet("background-color: red;")

        self.button_run.setEnabled(bool(sid_value))

    def input_sid(self):
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Ввод SID вручную")
        dialog.setLabelText("Введите SID:")
        dialog.resize(400, 100)
        done = dialog.exec()

        if done:
            self.set_sid(dialog.textValue())

    async def async_call_worker(self, call_type: CallType, payload, func):
        result = await self.callback(call_type, payload)
        func(result)

    def try_login(self):
        self.call_worker(CallType.LOGIN, None, self.set_sid)

    def try_search(self):
        return
        # not working
        # lst = get_sid_list()
        lst = ["sid1", "sid2", "sid3"]
        dlg = ListSelectDialog(lst, "Найдены cookies c SID")
        done = dlg.exec()
        print(done)
        if done:
            data = dlg.get_data()
            self.set_sid(data[1])

        # # sid_list = get_sid_list()
        # # здесь должен быть код получения списка найденых SID
        # dlg = QDialog(self)
        # dlg.setWindowTitle("Выбор SID")
        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        #
        # buttonBox = QDialogButtonBox(QBtn)

    def run_loading(self):
        def select_books(lst):
            print(lst)

        #self.callback(CallType.LOAD_BOOKS, None)
        self.call_worker(CallType.LOAD_BOOKS, self.sid, select_books)


def gui_run(callback_function: callable):
    app = QApplication([])
    main_window = MainWindow(callback_function)
    main_window.show()
    sys.exit(app.exec())
