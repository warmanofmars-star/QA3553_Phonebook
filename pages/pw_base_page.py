import allure
import os
from playwright.sync_api import Page, Locator
from utils.logger import get_logger


class PwBasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = "https://telranedu.web.app"

        # Динамический парсинг переменной из .env с фоллбэком
        pw_timeout = os.getenv("PW_TIMEOUT", "10000")
        self.expect_timeout = int(pw_timeout)

        # Подключаем логгер с уникальным именем для Playwright
        self.logger = get_logger("PW")

    def open_url(self, path: str = ""):
        url = f"{self.base_url}{path}"
        self.logger.info(f"Переход по ссылке: {url}")

        with allure.step(f"Открытие URL: {url}"):
            self.page.goto(url)

    def fill(self, locator: Locator, value: str, is_secret: bool = False):
        """Универсальный метод ввода с логированием и маскировкой Allure"""
        display_value = "********" if is_secret else value

        self.logger.info("Ввод данных в поле формы...")
        with allure.step(f"Ввод текста '{display_value}'"):
            locator.fill(value)

    def click(self, locator: Locator, element_name: str = "Элемент"):
        """Универсальный клик с логированием"""
        self.logger.info(f"Клик по элементу: '{element_name}'")

        with allure.step(f"Клик по элементу: {element_name}"):
            locator.click()