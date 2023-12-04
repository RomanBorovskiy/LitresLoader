import logging
from enum import Enum
from pathlib import Path

MAIN_URL = "https://www.litres.ru"
MY_BOOKS_URL = "https://www.litres.ru/pages/my_books_fresh/"  # первая страница с книгам
BOOK_N_PAGE_URL = "https://www.litres.ru/pages/my_books_fresh/page-{}/"  # следующие страницы
API_FILES_URL = "https://api.litres.ru/foundation/api/arts/{book_id}/files"  # API для списка книг
DOWNLOAD_FILES_URL = "https://www.litres.ru/download_book/{book_id}/{file_id}/{file_name}"  # url для скачивания


class EncodingTypes(str, Enum):
    """Типы данных - утащил из JS с litres.ru
    Возможно будут поменять, поэтом сюда разместил
    """

    INTRODUCTORY_FRAGMENT_MP3 = "introductory_fragment_mp3"
    ORIGINAL_DISK_COPY_MP3_RAR = "original_disk_copy_mp3_rar"
    STANDARD_QUALITY_MP3_128KBPS = "standard_quality_mp3_128kbps"
    MOBILE_VERSION_MP4_16_KBPS = "mobile_version_mp4_16_kbps"
    STANDARD_QUALITY_MP3 = "standard_quality_mp3"
    MOBILE_VERSION_MP4_32_KBPS = "mobile_version_mp4_32_kbps"
    STANDARD_QUALITY_MP3_64KBPS = "standard_quality_mp3_64kbps"
    ADDITIONAL_MATERIALS_MP3 = "additional_materials_mp3"
    MOBILE_VERSION_MP4 = "mobile_version_mp4"
    ZIP_WITH_MP3 = "zip_with_mp3"
    INTRODUCTORY_FRAGMENT_PDF = "introductory_fragment_pdf"
    PDF_BOOK = "pdf_book"
    COVER_PDF = "cover_pdf"
    ADDITIONAL_MATERIALS_PDF = "additional_materials_pdf"
    ADDITIONAL_MATERIALS_TXT = "additional_materials_txt"
    EPUB_BOOK = "epub_book"
    INTRODUCTORY_FRAGMENT_EPUB = "introductory_fragment_epub"
    ADDITIONAL_MATERIALS_EPUB = "additional_materials_epub"


#  типы данных, которые будем скачивать. Фрагменты и ознакомительные части нас не интересуют
USED_TYPES = {
    EncodingTypes.ZIP_WITH_MP3: "MP3",
    EncodingTypes.MOBILE_VERSION_MP4: "MP4",
    EncodingTypes.PDF_BOOK: "PDF",
}

# на что ориентируемся при парсинге страницы входа
PROFILE_TEXT = "Профиль"
ENTER_TEXT = "Войти"
COOKIE_SID_KEY = "SID"
COOKIE_AGREEMENT = {"name": "cookie-agreement", "value": "1", "domain": "www.litres.ru"}

# настройки - что можно и поменять
LOGGING_LEVEL = logging.DEBUG
DOWNLOAD_PATH = Path(__file__).parent.parent / "download"  # путь для скачивания
CHUNK_SIZE = 2**15  # 32кб размер частей для скачивания
CONCURRENCY = 10  # одновременно будет скачиваться книг
