import datetime
import logging
from datetime import timedelta

import requests
import requests.cookies
import selenium.webdriver.remote.webdriver

# import httpx
import asyncio
import aiohttp

from bs4 import BeautifulSoup
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

main_url = "https://www.litres.ru"
# login_url = "https://www.litres.ru/pages/login/"
my_books_url = "https://www.litres.ru/pages/my_books_fresh/"

expires = datetime.datetime.now() + timedelta(days=365)
cookie_agreement = {
    "name": "cookie-agreement",
    "value": "1",
    "path": "/",
    "domain": "www.litres.ru",
    "secure": False,
    "httpOnly": False,
    "expiry": int(expires.timestamp()),
    "sameSite": "None",
}
cookie_sid = {
    "name": "SID",
    "value": "6f305efu4072555n4m65df1ja60qfqew",
    "path": "/",
    "domain": "www.litres.ru",
    "secure": False,
    "httpOnly": False,
    "expiry": int(expires.timestamp()),
    "sameSite": "None",
}

logging.basicConfig(level=logging.DEBUG)


class Book(BaseModel):
    title: str
    author: str
    url: str
    links: dict[str, str]
    media_type: str


# driver = webdriver.Firefox()
def clear_string(s: str) -> str:
    return s.strip()


def init_driver() -> selenium.webdriver.remote.webdriver.WebDriver:
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # driver = webdriver.Firefox()
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)  # seconds

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def init_session(sid_value: str) -> requests.Session:
    session = requests.Session()
    session.cookies.set("SID", sid_value)
    return session


def load_cookies(driver, cookie: dict | list[dict]):
    driver.execute_cdp_cmd("Network.enable", {})
    if type(cookie) is list:
        for el in cookie:
            driver.execute_cdp_cmd("Network.setCookie", el)
            print("load cookie:" + el)
    else:
        driver.execute_cdp_cmd("Network.setCookie", cookie)

    driver.execute_cdp_cmd("Network.disable", {})


def get_sid_by_login(driver) -> str:
    load_cookies(driver, cookie_agreement)
    driver.get(main_url)

    login_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Войти")))
    login_btn.click()

    WebDriverWait(driver, 60 * 60 * 24).until(EC.element_to_be_clickable((By.LINK_TEXT, "Профиль")))

    sid = driver.get_cookie("SID")
    return sid["value"]


def get_page(session, page_number=1) -> requests.Response:
    if page_number > 1:
        page_url = my_books_url + f"page-{page_number}/"
    else:
        page_url = my_books_url

    result = session.get(page_url)

    return result


def get_pages_count(page_html: str):
    bs = BeautifulSoup(page_html, "html.parser")
    div_books = bs.find("div", {"class": "books_container"})
    pages_count = int(float(div_books["data-pages"]))
    return pages_count


def get_books(page_html: str) -> list[Book]:
    """Парсит страницу на список книг"""
    result = []

    bs = BeautifulSoup(page_html, "html.parser")

    books_box = bs.find("div", {"class": "books_box"})
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
                    clear_string(link.text): link["href"] for link in links if "art-download__more" not in link["class"]
                }

        current_book = Book(title=title, author=author, url=href, links=links_dict, media_type=data_type)
        result.append(current_book)

    return result


# def get_book_page_info(session: requests.Session, book: Book) -> dict:
def get_book_page_info(html: str) -> dict:
    """Получает данные со страницы книги. Требуется если нет информации для загрузки на общей странице."""
    # url = book.url
    links_dict = {}
    # result = session.get(main_url + url)

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


async def load_empty_links(books: list[Book], sid: str):
    async def get_async(book: Book):
        cookie = {"SID": sid}
        async with aiohttp.ClientSession(cookies=cookie) as session:
            async with session.get(url=main_url + book.url) as response:
                text = await response.text()

                links = get_book_page_info(text)
                book.links = links
                logging.info("loading for {0}".format(book.title))
                return bool(links)

    async def do_work():
        tasks = [asyncio.create_task(get_async(book)) for book in books if not book.links]
        result = await asyncio.gather(*tasks)
        return result

    return await do_work()


async def main():
    driver = 0
    session = 0
    # driver = init_driver()
    try:
        # sid = get_sid_by_login(driver)
        # print(sid)
        sid = "68ba5b2a4zas6d5o8ydzcnb1d91557bo"
        logging.info("use sid:{0}".format(sid))
        session = init_session(sid)

        logging.info("load page 1")
        page = get_page(session)

        pages_count = get_pages_count(page.text)
        books = get_books(page.text)

        if pages_count > 1:
            for page_num in range(2, pages_count + 1):
                logging.info("load page {0}".format(page_num))

                page = get_page(session, page_num)
                books_from_page = get_books(page.text)

                books.extend(books_from_page)

        logging.debug("find books, count:{0}".format(len(books)))

        logging.info("Добавляем данные")
        await load_empty_links(books, sid)
        print("after await")

        urls = [main_url + book.links["FB2"] for book in books if book.links.get("FB2")]

        print(urls)
        # for i, book in enumerate(books):
        # print(book)
        # print(f'{i} {book.title} - {book.author} {",".join(book.links.keys()) if book.links else "НЕТ ССЫЛОК"}')

    finally:
        if driver:
            driver.close()
        if session:
            session.close()


if __name__ == "__main__":
    asyncio.run(main())
