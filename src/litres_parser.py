import asyncio
import logging
from http import HTTPStatus

import aiohttp
import requests
from bs4 import BeautifulSoup
from src.constants import (API_FILES_URL, BOOK_N_PAGE_URL, COOKIE_SID_KEY, DOWNLOAD_FILES_URL, LOGGING_LEVEL, MAIN_URL,
                           MY_BOOKS_URL, USED_TYPES)
from src.models import Book

logging.basicConfig(level=LOGGING_LEVEL)


def clear_string(s: str) -> str:
    "Обработка строки - удаление символов форматирования и лишних пробелов"
    return s.strip()


class LitresPaser:
    """Парсер книг на сайте litres.ru

    sid - SID аккаунта
    try_load_empty - попытаться загрузить пути со страницы книги (актуально для аудиокниг и пдф-книг)
    """

    session: requests.Session = None
    page_count = -1
    books: list[Book] = []

    def __init__(self, sid: str, try_load_empty: bool = True):
        self.try_load_empty = try_load_empty
        self.sid_value = sid

    def _init_session(self):
        self.session = requests.Session()
        self.session.cookies.set(COOKIE_SID_KEY, self.sid_value)

    def _close_session(self):
        if self.session:
            self.session.close()

    def _get_page(self, page_number=1) -> str:
        if page_number > 1:
            page_url = BOOK_N_PAGE_URL.format(page_number)
        else:
            page_url = MY_BOOKS_URL

        response = self.session.get(page_url)
        if response.status_code == HTTPStatus.OK:
            result = response.text
        else:
            result = ""
            logging.error("book page {0} not found. Error {1}".format(page_number, response.status_code))
        return result

    @staticmethod
    def _get_pages_count(page_html: str) -> int:
        """Получает количество страниц в списке книг.
        Для этого парсится страница. Как правило, первая"""

        bs = BeautifulSoup(page_html, "html.parser")

        div_books = bs.find("div", {"class": "books_container"})
        if not div_books:
            logging.debug("not found div_books")
            return 0

        pages_count = int(float(div_books["data-pages"]))
        logging.debug("pages_count: " + str(pages_count))
        return pages_count

    @staticmethod
    def _get_books(page_html: str) -> list[Book]:
        """Парсит страницу и возвращает список книг"""
        result = []

        bs = BeautifulSoup(page_html, "html.parser")

        books_box = bs.find("div", {"class": "books_box"})
        if not books_box:
            logging.debug("not found books_box")
            return []

        books = books_box.find_all("div", {"class": "art-standart"})

        for book in books:
            author = "Нет"
            title = "Нет"
            href = ""
            book_id = ""
            links_dict = {}

            author_div = book.find("div", {"class": "art__author"})
            name_a = book.find("a", {"class": "art__name__href"})
            download_div = book.find("div", {"class": "art-buttons__download"})

            data_type = book.find("a", {"class": "img-a"})["data-type"]

            if author_div and author_div.a:
                author = clear_string(author_div.a["title"])

            if name_a:
                title = clear_string(name_a["title"])
                href = MAIN_URL + name_a["href"]
                # получаем ID книги из URL - а как еще?
                book_id = name_a["href"].split("-")[-1].replace("/", "")

            if download_div:
                links = download_div.find_all("a", {"class": "art-download__format"})
                if links:
                    links_dict = {
                        clear_string(link.text): MAIN_URL + link["href"]
                        for link in links
                        if "art-download__more" not in link["class"]
                    }

            current_book = Book(
                ident=book_id, title=title, author=author, url=href, links=links_dict, media_type=data_type
            )
            result.append(current_book)

        return result

    @staticmethod
    def _get_book_page_info(html: str) -> dict:
        """Получает данные со страницы книги. Требуется если нет информации для загрузки на общей странице."""
        links_dict = {}

        bs = BeautifulSoup(html, "html.parser")
        # links = bs.find_all("a", {"class": "biblio_book_download_file__link"})
        links = bs.find_all("a", {"data-analytics-id": "download-button"})

        if links:
            links_dict = {clear_string(link.span.string).upper(): MAIN_URL + link["href"] for link in links}
            logging.debug("links_dict: " + str(links_dict))
        else:
            logging.error("not found links")

        # бывают особые книги - пдф называются. У них только одна ссылка на скачивание.
        # может бывают еще и другие виды, но я их пока не видел
        pdf_button = bs.find("div", {"data-type": "pdf"})
        if pdf_button and pdf_button.a:
            links_dict["PDF"] = MAIN_URL + pdf_button.a["href"]

        return links_dict

    async def load_empty_links(self):
        cookie = {COOKIE_SID_KEY: self.sid_value}

        async def get_async(book: Book):
            async with aiohttp.ClientSession(cookies=cookie) as session:
                async with session.get(url=book.url) as response:
                    if response.status != HTTPStatus.OK:
                        logging.error(
                            "Error loading extra links for {0}, status: {1}".format(book.title, response.status)
                        )
                        return False

                    text = await response.text()
                    links = self._get_book_page_info(text)
                    book.links = links
                    logging.info("loading extra links for {0}".format(book.title))
                    return bool(links)

        tasks = [asyncio.create_task(get_async(book)) for book in self.books if not book.links]
        result = await asyncio.gather(*tasks)
        return result

    async def load_empty_links_api(self):
        cookie = {COOKIE_SID_KEY: self.sid_value}

        async def get_async(book: Book):
            logging.info(f"book: {book}")
            api_url = API_FILES_URL.format(book_id=book.ident)

            async with aiohttp.ClientSession(cookies=cookie) as session:
                async with session.get(url=api_url) as response:
                    if response.status != HTTPStatus.OK:
                        logging.error(
                            "Error loading extra links for {0}, status: {1}".format(book.title, response.status)
                        )
                        return False

                    json_files = await response.json()

                    if (json_files.get("status") != 200) or (not json_files.get("payload")):
                        logging.error(
                            "Error loading extra links for {0}, error: {1}".format(book.title, json_files["status"])
                        )
                        return False

                    payload = json_files["payload"]["data"]

                    links = {
                        USED_TYPES[data["encoding_type"]]: DOWNLOAD_FILES_URL.format(
                            book_id=book.ident, file_id=data["id"], file_name=data["filename"]
                        )
                        for data in payload
                        if data["encoding_type"] in USED_TYPES
                    }

                    logging.debug(f"links:{links}")
                    book.links = links
                    logging.info("loading extra links for {0}".format(book.title))
                    return bool(links)

        tasks = [asyncio.create_task(get_async(book)) for book in self.books if not book.links]
        result = await asyncio.gather(*tasks)
        return result

    async def do_parse(self) -> list[Book]:
        """Основная функция.
        Все парсим, возвращаем список книг. Ну и в классе храним заодно"""

        self._init_session()
        try:
            page_html = self._get_page()
            self.page_count = self._get_pages_count(page_html)
            if self.page_count < 1:
                logging.error("no books pages found")
                return []

            logging.info("load main page")
            self.books = self._get_books(page_html)
            if self.page_count > 1:
                for page_num in range(2, self.page_count + 1):
                    logging.info("load page {0}".format(page_num))

                    page_html = self._get_page(page_num)
                    books_from_page = self._get_books(page_html)

                    self.books.extend(books_from_page)

        finally:
            self._close_session()

        if self.try_load_empty:
            await self.load_empty_links_api()

        self.books.sort(key=lambda x: x.title)
        return self.books
