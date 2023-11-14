import asyncio
import functools
import sys
from enum import Enum
from functools import partial

import PyQt5.QtCore as QtCore
import qasync
from PyQt5.QtWidgets import (QDesktopWidget, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QInputDialog, QLabel,
                             QListWidget, QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)
from qasync import QApplication, asyncSlot


# callback = function(id:int, payload)
class CallType(Enum):
    LOGIN = 1
    SEARCH = 2
    LOAD_BOOKS = 3
    DOWNLOAD = 4


MEDIA_START_POS = 2


class ListSelectDialog(QDialog):
    """Диалог выбора элемента из списка - не используется сейчас"""

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
        self.self.layout_v.addWidget(self.lst_view)
        self.self.layout_v.addWidget(self.button_box)

        self.setLayout(self.layout)

        self.setWindowTitle(title)

        self.resize(300, 300)

    def get_data(self) -> tuple[int, str]:
        return self.lst_view.currentRow(), self.lst_view.item(self.lst_view.currentRow()).text()


class MainWindow(QMainWindow):
    def __init__(self, callback: callable):
        super().__init__()
        self.sid = ""
        self.books = []
        self.media_types = []

        self.callback = callback

        self.setWindowTitle("Загрузка книг с Litres")
        self.setGeometry(0, 0, 800, 600)

        # центруем окно
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)

        self.select_layout = QHBoxLayout()
        self.select_layout.setSpacing(10)

        # заголовки над кнопками
        labels_style = "border: 1px solid black; border-radius: 5px; background-color: khaki;"

        label_1 = QLabel("1. Получить доступ")
        label_1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label_1.setStyleSheet(labels_style)

        label_2 = QLabel("2. Загрузить список книг")
        label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label_2.setStyleSheet(labels_style)

        label_3 = QLabel("3. Скачать книги")
        label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label_3.setStyleSheet(labels_style)

        # кнопки для запуска
        self.button_login = QPushButton("Вход в ЛК Litres", self)
        self.button_search = QPushButton("*Искать в cookies*", self)
        self.button_search.setEnabled(False)  # не реализовано
        self.button_input = QPushButton("Ввести sid", self)

        self.sid_label = QLabel(self)
        self.sid_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.button_load_list = QPushButton("Загрузить список", self)
        self.button_load_list.setEnabled(False)

        self.button_download = QPushButton("Скачать книги", self)
        self.button_download.setEnabled(False)

        self.grid_layout.addWidget(label_1, 0, 0)
        self.grid_layout.addWidget(label_2, 0, 1)
        self.grid_layout.addWidget(label_3, 0, 2)
        self.grid_layout.addWidget(self.button_login, 1, 0)
        self.grid_layout.addWidget(self.button_search, 2, 0)
        self.grid_layout.addWidget(self.button_input, 3, 0)
        self.grid_layout.addWidget(self.sid_label, 1, 1)
        self.grid_layout.addWidget(self.button_load_list, 2, 1)
        self.grid_layout.addWidget(self.button_download, 1, 2)

        self.grid_layout.addLayout(self.select_layout, 4, 0, 1, 3)

        self.table = QTableWidget(self)
        self.grid_layout.addWidget(self.table, 5, 0, 1, 3)

        widget = QWidget()
        widget.setLayout(self.grid_layout)
        self.setCentralWidget(widget)

        self.set_sid("")
        self.set_books([])
        self.set_media_types([])

        self.button_login.clicked.connect(self.try_login)
        self.button_search.clicked.connect(self.try_search)
        self.button_input.clicked.connect(self.show_dialog_input_sid)
        self.button_load_list.clicked.connect(self.run_loading)
        self.button_download.clicked.connect(self.run_download)

    def set_sid(self, sid_value: str):
        if sid_value:
            self.sid_label.setText(sid_value)
            self.sid = sid_value
            self.sid_label.setStyleSheet("background-color: green; border-radius: 25px;border: 1px solid black;")
        else:
            self.sid_label.setText("No SID")
            self.sid_label.setStyleSheet("background-color: red; border-radius: 25px;border: 1px solid black;")

        self.button_load_list.setEnabled(bool(sid_value))

    def set_books(self, books_list):
        if books_list:
            self.books = books_list
            self.button_download.setEnabled(True)
        else:
            self.books = []
            self.button_download.setEnabled(False)

    def set_media_types(self, media_type_list):
        if media_type_list:
            self.media_types = media_type_list
        else:
            self.media_types = []
        self.set_select_buttons(self.media_types)

    def on_select_button_clicked(self, media_type: str):
        # print(media_type)
        if media_type == "all":
            for i in range(self.table.rowCount()):
                for j in range(MEDIA_START_POS, self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setCheckState(QtCore.Qt.CheckState.Checked)

        elif media_type == "none":
            for i in range(self.table.rowCount()):
                for j in range(MEDIA_START_POS, self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setCheckState(QtCore.Qt.CheckState.Unchecked)

        else:
            j = self.media_types.index(media_type)
            for i in range(self.table.rowCount()):
                item = self.table.item(i, j + MEDIA_START_POS)
                if item:
                    item.setCheckState(QtCore.Qt.CheckState.Checked)

    def set_select_buttons(self, media_type_list: list[str]):
        # удаляем все виджеты
        for i in reversed(range(self.select_layout.count())):
            self.select_layout.itemAt(i).widget().deleteLater()

        # если нет ни одного формата - не надо и кнопок "выбрать все" и "убрать все"
        if not media_type_list:
            return

        button_all = QPushButton("Выбрать все")
        button_all.setStyleSheet("background-color: cyan")
        button_all.clicked.connect(partial(self.on_select_button_clicked, "all"))
        self.select_layout.addWidget(button_all)

        button_none = QPushButton("Убрать все")
        button_none.setStyleSheet("background-color: cyan")
        button_none.clicked.connect(partial(self.on_select_button_clicked, "none"))
        self.select_layout.addWidget(button_none)

        for media_type in media_type_list:
            button = QPushButton(media_type)
            button.setStyleSheet("background-color: cyan")
            button.clicked.connect(partial(self.on_select_button_clicked, media_type))
            self.select_layout.addWidget(button)

    def show_books(self, books: list):
        # получаем все форматы
        self.set_books(books)
        media_types = set()
        for book in books:
            media_types.update(set(book.links.keys()))
        media_types = sorted(list(media_types))

        self.set_media_types(media_types)

        col_count = len(media_types) + MEDIA_START_POS

        self.setGeometry(300, 300, 800, 800)
        self.table.setRowCount(len(books))
        self.table.setColumnCount(col_count)

        self.table.setColumnWidth(0, 550)
        self.table.setColumnWidth(1, 150)

        for i in range(MEDIA_START_POS, col_count):
            self.table.setColumnWidth(i, 35)

        self.table.setHorizontalHeaderLabels(["Название", "Автор"] + media_types)
        for i, book in enumerate(books):
            self.table.setItem(i, 0, QTableWidgetItem(book.title))
            self.table.setItem(i, 1, QTableWidgetItem(book.author))
            for link in book.links:
                item = QTableWidgetItem()
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.CheckState.Checked)
                self.table.setItem(i, media_types.index(link) + MEDIA_START_POS, item)

        # self.centralWidget().layout().removeItem(self.stretcher)
        self.table.resizeColumnsToContents()

    def get_urls_of_selected_books(self):
        urls = []
        for i in range(self.table.rowCount()):
            for j in range(MEDIA_START_POS, self.table.columnCount()):
                item = self.table.item(i, j)
                if item and item.checkState() == QtCore.Qt.CheckState.Checked:
                    urls.append(self.books[i].links[self.media_types[j - MEDIA_START_POS]])
        return urls

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

    def run_download(self):
        def on_download_complete(result):
            count = result.count(True)
            QMessageBox.information(self, "Информация", f"Загрузка завершена ({count} книг из {len(result)})")

        urls = self.get_urls_of_selected_books()
        if urls:
            self.async_call_worker(CallType.DOWNLOAD, (self.sid, urls), on_download_complete)
        else:
            QMessageBox.warning(self, "Предупреждение", "Вы не выбрали ни одного элемента")


async def run_app(callback_function: callable):
    "Запускает интерфейс программы"

    # здесь - все согласно примера из доков к библиотеке
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
