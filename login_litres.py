import logging

import selenium.webdriver.remote.webdriver
from constants import COOKIE_AGREEMENT, COOKIE_SID, ENTER_TEXT, PROFILE_TEXT, MAIN_URL, LOGGING_LEVEL
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

logging.basicConfig(level=LOGGING_LEVEL)


class LitresSid:
    """Запускает сайт litres.ru, ждет входа в аккаунт и возвращает SID
    использование - LitresSid().get_sid()
    возвращает строку с SID или пустую строку
    """

    time_out: int = 20  #  ожидание загрузки страницы - 20 сек
    logging_timeout: int = 60 * 60  # ожидание входа - 1 час
    driver: selenium.webdriver.remote.webdriver.WebDriver

    def _init_driver(self):
        logging.debug("init driver")
        options = Options()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # driver = webdriver.Firefox()
        self.driver = webdriver.Chrome(options=options)
        stealth(self.driver, platform="Win32", fix_hairline=True, languages=["ru-RU"])

    def _load_cookies(self, cookie: dict | list[dict]):
        self.driver.execute_cdp_cmd("Network.enable", {})
        if type(cookie) is list:
            for el in cookie:
                self.driver.execute_cdp_cmd("Network.setCookie", el)
                logging.debug("load cookie:" + el)
        else:
            self.driver.execute_cdp_cmd("Network.setCookie", cookie)

        self.driver.execute_cdp_cmd("Network.disable", {})

    def _close_driver(self):
        if self.driver:
            self.driver.quit()

    def _get_sid_by_login(self) -> str:
        logging.debug("load main page")
        try:
            self.driver.get(MAIN_URL)
        except WebDriverException:
            logging.error("error while loading")
            return ""

        logging.debug("wait for end loading")
        try:
            login_btn = WebDriverWait(self.driver, self.time_out).until(
                EC.element_to_be_clickable((By.LINK_TEXT, ENTER_TEXT))
            )
            login_btn.click()
        except WebDriverException:
            logging.error("error while loading")
            return ""

        logging.debug("wait for logging...")
        try:
            WebDriverWait(self.driver, self.logging_timeout).until(
                EC.element_to_be_clickable((By.LINK_TEXT, PROFILE_TEXT))
            )
        except WebDriverException:
            logging.error("error while logging wait")
            return ""

        sid = self.driver.get_cookie(COOKIE_SID)

        if sid:
            sid_value = sid["value"]
            logging.debug("SID: " + sid["value"])
        else:
            sid_value = ""
            logging.debug("cookie SID not found")

        return sid_value

    def get_sid(self):
        self._init_driver()
        self._load_cookies(COOKIE_AGREEMENT)
        try:
            sid_value = self._get_sid_by_login()
            return sid_value
        finally:
            self._close_driver()
