import asyncio
import logging

import login_litres
import litres_parser
import fileloader
from constants import COOKIE_SID_KEY, MAIN_URL, LOGGING_LEVEL
from models import Book
from gui import gui_run, CallType

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
    print("enter cb", call_type, payload)
    match call_type:
        case CallType.LOGIN:
            #sid = get_sid()
            sid = "68ba5b2a4zas6d5o8ydzcnb1d91557bo"
            return sid

        case CallType.LOAD_BOOKS:
            books = await load_book_list(payload)
            print(books)
            return books

        case CallType.DOWNLOAD:
            pass

        case _:
            print("unknown call type")



async def main():
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
    asyncio.run(main())
