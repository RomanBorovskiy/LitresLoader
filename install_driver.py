import logging

from selenium.webdriver.common import selenium_manager

logging.basicConfig(level=logging.DEBUG)


def main():
    binary = selenium_manager.SeleniumManager.get_binary()
    if not binary.exists():
        logging.error("Binary of selenium-manager not found")
        return

    result = selenium_manager.SeleniumManager().run([str(binary), "--browser", "chrome"])
    if result["code"] != 0:
        logging.error(result["message"])
        return

    logging.info(f"driver:{result['driver_path']}      browser:{result['browser_path']}")


if __name__ == "__main__":
    main()
