import asyncio
import logging

import fileloader
import litres_parser
import login_litres
from constants import COOKIE_SID_KEY, LOGGING_LEVEL, MAIN_URL
from gui import CallType, gui_run
from models import Book

logging.basicConfig(level=LOGGING_LEVEL)


def get_sid() -> str:
    sid = login_litres.LitresSid().get_sid()
    return sid


async def load_book_list(sid: str) -> list:
    books = await litres_parser.LitresPaser(sid, True).do_parse()
    return books


async def download_books(sid: str, books: list[str]):
    cookie = {COOKIE_SID_KEY: sid}

    await fileloader.FileLoader(cookie=cookie, load_list=books).start()


def select_urls(books: list[Book]) -> list:
    book_list = [MAIN_URL + book.links["FB2"] for book in books if "FB2" in book.links]
    return book_list


async def gui_callback(call_type: CallType, payload):
    match call_type:
        case CallType.LOGIN:
            # sid = get_sid()
            sid = "68ba5b2a4zas6d5o8ydzcnb1d91557bo"
            return sid

        case CallType.LOAD_BOOKS:
            books = await load_book_list(payload)
            # books = [Book(title="test1", author="test_a1", url="test_url1", links={"FB2": "test"}, media_type="test"),
            #         Book(title="test2", author="test_a2", url="test_url2", links={"PDF": "test"}, media_type="test")]
            return books

        case CallType.DOWNLOAD:
            pass

        case _:
            print("unknown call type")


def main():
    gui_run(gui_callback)
    return
    # #sid = get_sid()
    # sid = "68ba5b2a4zas6d5o8ydzcnb1d91557bo"
    # books = await load_book_list(sid)
    # logging.info("found {0} books".format(len(books)))
    # book_list = select_urls(books)
    # #book_list = [MAIN_URL + book.links["FB2"] for book in books if "FB2" in book.links]
    #
    # await download_books(sid, book_list)
    # logging.info("downloaded {0} books".format(len(book_list)))


if __name__ == "__main__":
    main()
