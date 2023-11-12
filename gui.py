import asyncio
import functools
import sys
from enum import Enum

import PyQt5.QtCore as QtCore
import qasync
from PyQt5.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QInputDialog, QLabel, QListWidget,
                             QMainWindow, QPushButton, QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)
from qasync import QApplication, asyncSlot


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

        self.callback = callback

        self.setWindowTitle("Шаг 1. Получить SID")
        self.setGeometry(300, 300, 400, 200)
        # self.setFixedHeight(400)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.button_login = QPushButton("Вход в ЛК Litres", self)
        self.button_search = QPushButton("*Искать в cookies*", self)
        self.button_search.setEnabled(False)

        self.button_input = QPushButton("Ввести вручную", self)

        self.sid_label = QLabel(self)
        self.sid_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.sid_label.setStyleSheet("border-radius: 25px;border: 1px solid black;")

        self.button_run = QPushButton("Старт", self)
        self.button_run.setEnabled(False)

        layout.addWidget(self.button_login)
        layout.addWidget(self.button_search)
        layout.addWidget(self.button_input)
        layout.addWidget(self.sid_label)
        layout.addWidget(self.button_run)

        # self.stretcher = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # layout.addItem(self.stretcher)
        self.table = QTableWidget(self)
        layout.addWidget(self.table)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.set_sid("")

        self.button_login.clicked.connect(self.try_login)
        self.button_search.clicked.connect(self.try_search)
        self.button_input.clicked.connect(self.show_dialog_input_sid)
        self.button_run.clicked.connect(self.run_loading)

    def set_sid(self, sid_value: str):
        if sid_value:
            self.sid_label.setText(sid_value)
            self.sid = sid_value
            self.sid_label.setStyleSheet("background-color: green; border-radius: 25px;border: 1px solid black;")
        else:
            self.sid_label.setText("No SID")
            self.sid_label.setStyleSheet("background-color: red; border-radius: 25px;border: 1px solid black;")

        self.button_run.setEnabled(bool(sid_value))

    def show_books(self, books: list):
        links = set()
        for book in books:
            link = set(book.links.keys())
            links.update(set(book.links.keys()))

        links = list(links)
        col_count = len(links) + 2

        self.table.setRowCount(len(books))
        self.table.setColumnCount(col_count)
        self.setGeometry(300, 300, 800, 800)

        self.table.setColumnWidth(0, 550)
        self.table.setColumnWidth(1, 150)
        for i in range(2, col_count):
            self.table.setColumnWidth(i, 35)

        self.table.setHorizontalHeaderLabels(["Название", "Автор"] + links)
        for i, book in enumerate(books):
            self.table.setItem(i, 0, QTableWidgetItem(book.title))
            self.table.setItem(i, 1, QTableWidgetItem(book.author))
            for link in book.links:
                item = QTableWidgetItem()
                item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.CheckState.Checked)

                self.table.setItem(i, links.index(link) + 2, item)

        self.centralWidget().layout().removeItem(self.stretcher)
        # self.centralWidget().layout().addWidget(self.table)
        self.table.resizeColumnsToContents()
        # self.layout().addWidget(self.table)

    def show_dialog_input_sid(self):
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setWindowTitle("Ввод SID вручную")
        dialog.setLabelText("Введите SID:")
        dialog.resize(400, 100)
        done = dialog.exec()

        if done:
            self.set_sid(dialog.textValue())

    @asyncSlot()
    async def async_call_worker(self, call_type: CallType, payload, func):
        result = await self.callback(call_type, payload)
        func(result)

    def try_login(self):
        self.async_call_worker(CallType.LOGIN, None, self.set_sid)

    def try_search(self):
        return
        # not working yet)))
        # lst = get_sid_list()
        # lst = ["sid1", "sid2", "sid3"]
        # dlg = ListSelectDialog(lst, "Найдены cookies c SID")
        # done = dlg.exec()
        # print(done)
        # if done:
        #     data = dlg.get_data()
        #     self.set_sid(data[1])

    def run_loading(self):
        self.async_call_worker(CallType.LOAD_BOOKS, self.sid, self.show_books)


async def run_app(callback_function: callable):
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(functools.partial(close_future, future, loop))

    main_window = MainWindow(callback_function)
    main_window.show()

    await future
    return True


def gui_run(callback_function: callable):
    try:
        qasync.run(run_app(callback_function))

    except asyncio.exceptions.CancelledError:
        sys.exit(0)
