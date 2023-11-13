import logging

from src import fileloader, login_litres, litres_parser
from src.constants import COOKIE_SID_KEY, LOGGING_LEVEL, MAIN_URL
from src.gui import CallType, gui_run
from src.models import Book

logging.basicConfig(level=LOGGING_LEVEL)


def get_sid() -> str:
    sid = login_litres.LitresSid().get_sid()
    return sid


async def load_book_list(sid: str) -> list:
    books = await litres_parser.LitresPaser(sid, True).do_parse()
    return books


async def download_books(sid: str, books: list[str]):
    cookie = {COOKIE_SID_KEY: sid}

    return await fileloader.FileLoader(cookie=cookie, load_list=books).start()


def select_urls(books: list[Book]) -> list:
    book_list = [MAIN_URL + book.links["FB2"] for book in books if "FB2" in book.links]
    return book_list


async def gui_callback(call_type: CallType, payload):
    match call_type:
        case CallType.LOGIN:
            sid = get_sid()
            # sid = "68ba5b2a4zas6d5o8ydzcnb1d91557bo"
            return sid

        case CallType.LOAD_BOOKS:
            books = await load_book_list(payload)
            return books

        case CallType.DOWNLOAD:
            sid = payload[0]
            book_list = payload[1]
            result = await download_books(sid, book_list)
            return result

        case _:
            print("unknown call type")


def main():
    gui_run(gui_callback)


if __name__ == "__main__":
    main()
