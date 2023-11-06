import datetime
import logging
from pydantic import BaseModel

from bs4 import BeautifulSoup
from selenium import webdriver, common
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

from selenium.webdriver.common.keys import Keys
import time
from datetime import timedelta
import requests

main_url = 'https://www.litres.ru'
login_url = 'https://www.litres.ru/pages/login/'
my_books_url = 'https://www.litres.ru/pages/my_books_fresh/'

expires = datetime.datetime.now() + timedelta(days=365)
cookie_agreement = {'name': 'cookie-agreement', 'value': '1', 'path': '/', 'domain': 'www.litres.ru',
                    'secure': False, 'httpOnly': False, 'expiry': int(expires.timestamp()), 'sameSite': 'None'}
cookie_sid = {'name': 'SID', 'value': '6f305efu4072555n4m65df1ja60qfqew', 'path': '/', 'domain': 'www.litres.ru',
              'secure': False, 'httpOnly': False, 'expiry': int(expires.timestamp()), 'sameSite': 'None'}

logging.basicConfig(level=logging.DEBUG)


class Book(BaseModel):
    title: str
    author: str
    url: str
    links: dict[str, str]
    type: str


# login_url = 'https://ya.ru'
# driver = webdriver.Firefox()


def init_driver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # driver = webdriver.Firefox()
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)  # seconds

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


def load_cookies(driver, cookie: dict | list[dict]):
    driver.execute_cdp_cmd('Network.enable', {})
    if type(cookie) is list:
        for el in cookie:
            driver.execute_cdp_cmd('Network.setCookie', el)
            print('load cookie:' + el)
    else:
        driver.execute_cdp_cmd('Network.setCookie', cookie)

    driver.execute_cdp_cmd('Network.disable', {})


def get_sid_by_login(driver) -> str:
    load_cookies(driver, cookie_agreement)
    driver.get(main_url)
    # driver.get(login_url)
    # driver.add_cookie(cookie_agreement)
    # driver.add_cookie(cookie_sid)
    # driver.add_cookie(cookie_agreement)

    # cookies_ok_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div/div/button")
    # #cookies_ok_btn = WebDriverWait(driver, 20).until(
    # #    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[3]/div/div/div/button")))
    # cookies_ok_btn.click()

    login_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Войти")))
    # login_btn = driver.find_element(By.LINK_TEXT, "Войти")
    login_btn.click()

    login_btn = WebDriverWait(driver, 60 * 60 * 24).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Профиль")))
    # # print(login_btn)
    # entered = None
    # while not entered:
    #     try:
    #         entered = driver.find_element(By.LINK_TEXT, "Профиль")
    #     except common.exceptions.NoSuchElementException:
    #         pass

    sid = driver.get_cookie('SID')
    return sid['value']


def get_page(driver, sid_cookie, page_number=1) -> requests.Response:
    # driver.get(main_url)
    # ookie_sid['value'] = sid
    session = requests.Session()
    # r = session.get(page_url)
    # print(r.text)
    # session.cookies.set_cookie(sid_cookie)
    if page_number > 1:
        page_url = my_books_url + f'page-{page_number}/'
    else:
        page_url = my_books_url

    result = session.get(page_url, cookies=sid_cookie)

    print(session.cookies.get_dict())
    # r = requests.get(page_url, cookies=sid_cookie)
    # print(result.text)
    return result


def get_pages_count(page_html: str):
    bs = BeautifulSoup(page_html, "html.parser")
    div_books = bs.find('div', {"class": "books_container"})
    data_pages = div_books['data-pages'] or '1'
    pages_count = int(float(div_books['data-pages']))
    return pages_count


def get_books(page_html: str) -> list[Book]:
    """Парсит страницу на список книг"""
    result = []

    bs = BeautifulSoup(page_html, "html.parser")

    books_box = bs.find('div', {"class": "books_box"})
    books = books_box.find_all('div', {"class": "art-standart"})

    for book in books:
        author = 'Нет'
        title = 'Нет'
        href = ''
        links_dict = {}

        author_div = book.find('div', {'class': 'art__author'})
        name_a = book.find('a', {'class': 'art__name__href'})
        download_div = book.find('div', {'class': "art-buttons__download"})

        data_type = book.find('a', {'class': "img-a"})['data-type']

        if author_div and author_div.a:
            author = author_div.a['title']

        if name_a:
            title = name_a['title']
            href = name_a['href']

        if download_div:
            links = download_div.find_all('a', {"class": "art-download__format"})
            if links:
                links_dict = {link.text: link['href'] for link in links if 'art-download__more' not in link['class']}

        current_book = Book(title=title, author=author, url=href, links=links_dict, type=data_type)
        result.append(current_book)

    return result

def get_book_page_info(book:Book) -> dict:
    """Получает данные со страницы книги. Требуется если нет информации для загрузки на общей странице. """

def main():
    driver = 0
    # driver = init_driver()
    try:
        # sid = get_sid_by_login(driver)
        # print(sid)
        sid = {'domain': 'www.litres.ru', 'expiry': '1733679099', 'httpOnly': 'False', 'name': 'SID', 'path': '/',
               'sameSite': 'Lax', 'secure': 'False', 'value': '67845z5p4z2s6x6j7tf9ft36c494a8cy'}

        sid = {'SID': "68ba5b2a4zas6d5o8ydzcnb1d91557bo"}

        logging.info('load page 1')
        page = get_page(driver, sid)
        pages_count = get_pages_count(page.text)
        books = get_books(page.text)

        if pages_count > 1:
            for page_num in range(2, pages_count + 1):
                logging.info('load page {0}'.format(page_num))
                page = get_page(driver, sid, page_num)
                books_from_page = get_books(page.text)
                books.extend(books_from_page)

        for book in books:
            print(book)
        logging.debug('find books, count:{0}'.format(len(books)))
        # while True:
        #     time.sleep(.1)
    finally:
        # driver.close()
        pass


if __name__ == '__main__':
    main()
