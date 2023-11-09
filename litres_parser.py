import logging
import aiohttp
import asyncio
import requests
from constants import MY_BOOKS_URL, BOOK_N_PAGE_URL, COOKIE_SID, MAIN_URL, LOGGING_LEVEL
from bs4 import BeautifulSoup
from models import Book


logging.basicConfig(level=LOGGING_LEVEL)


def clear_string(s: str) -> str:
    return s.strip()


class LitresPaser:
    session: requests.Session = None
    page_count = -1
    books: list[Book] = []

    def __init__(self, sid: str, load_empty: bool = True):
        self.load_empty = load_empty
        self.sid_value = sid

    def _init_session(self):
        self.session = requests.Session()
        self.session.cookies.set(COOKIE_SID, self.sid_value)

    def _close_session(self):
        if self.session:
            self.session.close()

    def _get_page(self, page_number=1) -> str:
        if page_number > 1:
            page_url = BOOK_N_PAGE_URL.format(page_number)
        else:
            page_url = MY_BOOKS_URL

        result = self.session.get(page_url).text

        return result

    @staticmethod
    def _get_pages_count(page_html: str) -> int:
        bs = BeautifulSoup(page_html, "html.parser")

        div_books = bs.find("div", {"class": "books_container"})
        pages_count = int(float(div_books["data-pages"]))
        logging.debug("pages_count: " + str(pages_count))
        return pages_count

    @staticmethod
    def _get_books(page_html: str) -> list[Book]:
        """Парсит страницу на список книг"""
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
            links_dict = {}

            author_div = book.find("div", {"class": "art__author"})
            name_a = book.find("a", {"class": "art__name__href"})
            download_div = book.find("div", {"class": "art-buttons__download"})

            data_type = book.find("a", {"class": "img-a"})["data-type"]

            if author_div and author_div.a:
                author = clear_string(author_div.a["title"])

            if name_a:
                title = clear_string(name_a["title"])
                href = name_a["href"]

            if download_div:
                links = download_div.find_all("a", {"class": "art-download__format"})
                if links:
                    links_dict = {
                        clear_string(link.text): link["href"]
                        for link in links
                        if "art-download__more" not in link["class"]
                    }

            current_book = Book(title=title, author=author, url=href, links=links_dict, media_type=data_type)
            result.append(current_book)

        return result

    @staticmethod
    def _get_book_page_info(html: str) -> dict:
        """Получает данные со страницы книги. Требуется если нет информации для загрузки на общей странице."""
        links_dict = {}

        bs = BeautifulSoup(html, "html.parser")
        links = bs.find_all("a", {"class": "biblio_book_download_file__link"})

        if links:
            links_dict = {clear_string(link.span.string): link["href"] for link in links}

        # бывают особые книги - пдф называются. У них только одна ссылка на скачивание.
        # может бывают еще и другие виды, но я их пока не видел
        pdf_button = bs.find("div", {"data-type": "pdf"})
        if pdf_button and pdf_button.a:
            links_dict["PDF"] = pdf_button.a["href"]

        return links_dict

    async def load_empty_links(self):
        cookie = {COOKIE_SID: self.sid_value}

        async def get_async(book: Book):
            async with aiohttp.ClientSession(cookies=cookie) as session:
                async with session.get(url=MAIN_URL + book.url) as response:
                    text = await response.text()

                    links = self._get_book_page_info(text)
                    book.links = links
                    logging.info("loading extra links for {0}".format(book.title))
                    return bool(links)

        tasks = [asyncio.create_task(get_async(book)) for book in self.books if not book.links]
        result = await asyncio.gather(*tasks)
        return result

    async def do_parse(self):
        self._init_session()
        try:
            page_html = self._get_page()
            self.page_count = self._get_pages_count(page_html)
            if self.page_count < 1:
                logging.error("no books pages found")
                return []

            self.books = self._get_books(page_html)
            if self.page_count > 1:
                for page_num in range(2, self.page_count + 1):
                    logging.debug("load page {0}".format(page_num))

                    page_html = self._get_page(page_num)
                    books_from_page = self._get_books(page_html)

                    self.books.extend(books_from_page)

        finally:
            self._close_session()

        if self.load_empty:
            await self.load_empty_links()

        return self.books
