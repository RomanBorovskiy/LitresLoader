import logging
from pathlib import Path

MAIN_URL = "https://www.litres.ru"
MY_BOOKS_URL = "https://www.litres.ru/pages/my_books_fresh/"  # первая страница с книгам
BOOK_N_PAGE_URL = "https://www.litres.ru/pages/my_books_fresh/page-{}/"  # следующие страницы

# на что ориентируемся при парсинге страницы входа
PROFILE_TEXT = "Профиль"
ENTER_TEXT = "Войти"
COOKIE_SID_KEY = "SID"
COOKIE_AGREEMENT = {"name": "cookie-agreement", "value": "1", "domain": "www.litres.ru"}

# настройки - что можно и поменять
LOGGING_LEVEL = logging.INFO
DOWNLOAD_PATH = Path(__file__).parent.parent / "download"  # путь для скачивания
CHUNK_SIZE = 2**15  # 32кб размер частей для скачивания
