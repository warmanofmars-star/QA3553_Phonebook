"""
Базовый класс Selenium Page Object.

Два уровня методов:
  * _find, _click, _fill, _is_visible... (с подчёркиванием) — внутренняя механика:
    ожидания и работа с локаторами. Шагов в Allure НЕ создают (действия и так
    логирует listener) и не предназначены для вызова из тестов.
  * Публичные методы страниц-наследников — действия пользователя ("Нажать Save",
    "Открыть карточку контакта"). Каждый — один понятный шаг в отчёте через @step.

Тест работает только с публичными методами и не знает ни про локаторы, ни про WebDriverWait.
"""

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from config import settings
from utils.allure_steps import step
from utils.logger import get_logger

Locator = tuple[str, str]


class BasePage:
    BASE_URL = settings.base_url
    ENDPOINT = ""
    PAGE_NAME = "страница"           # человеческое имя для шагов отчёта; задаётся в наследниках
    DEFAULT_TIMEOUT = settings.ui_timeout

    # Общий для всех страниц элемент шапки
    _SIGN_OUT_BTN = (By.XPATH, "//button[text()='Sign Out']")

    def __init__(self, driver):
        self.driver = driver
        self.logger = get_logger("UI")

    # ==========================================
    # Публичные действия, общие для всех страниц
    # ==========================================
    def open(self) -> None:
        url = f"{self.BASE_URL}{self.ENDPOINT}"
        with allure.step(f"Открыть страницу «{self.PAGE_NAME}»"):
            self.logger.info(f"Открываем страницу: {url}")
            self.driver.get(url)

    @step("Нажать Sign Out")
    def sign_out(self) -> None:
        self._click(self._SIGN_OUT_BTN)

    def is_signed_in(self, timeout: float | None = None) -> bool:
        """Пользователь авторизован — в шапке есть кнопка Sign Out."""
        return self._is_visible(self._SIGN_OUT_BTN, timeout)

    def is_url_contains(self, fragment: str, timeout: float | None = None) -> bool:
        """Ждёт, пока адрес страницы будет содержать fragment (например, после редиректа)."""
        try:
            self._wait(timeout).until(EC.url_contains(fragment))
            return True
        except TimeoutException:
            return False

    # ---------- Alert ----------
    def wait_for_alert_text(self, timeout: float | None = None) -> str | None:
        """Ждёт Alert и возвращает его текст, а если он не появился — None.

        Не бросает TimeoutException: отсутствие алерта проверяется в тесте обычным
        assert, и тогда провал корректно попадает в known_bug (там только AssertionError).
        """
        with allure.step("Дождаться Alert"):
            try:
                alert = self._wait(timeout).until(EC.alert_is_present())
            except TimeoutException:
                self.logger.info("Alert не появился")
                return None
            self.logger.info(f"Текст Alert: '{alert.text}'")
            return alert.text

    @step("Закрыть Alert (OK)")
    def accept_alert(self) -> None:
        self._wait().until(EC.alert_is_present()).accept()

    # ==========================================
    # Внутренняя механика (для наследников)
    # ==========================================
    def _wait(self, timeout: float | None = None) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout or self.DEFAULT_TIMEOUT)

    def _find(self, locator: Locator) -> WebElement:
        """Элемент, присутствующий в DOM."""
        return self._wait().until(EC.presence_of_element_located(locator))

    def _find_visible(self, locator: Locator) -> WebElement:
        return self._wait().until(EC.visibility_of_element_located(locator))

    def _click(self, locator: Locator) -> None:
        self._wait().until(EC.element_to_be_clickable(locator)).click()

    def _fill(self, locator: Locator, value: str) -> None:
        element = self._find_visible(locator)
        element.clear()
        element.send_keys(value)

    def _count(self, locator: Locator) -> int:
        """Сколько элементов найдено прямо сейчас (без ожидания)."""
        return len(self.driver.find_elements(*locator))

    def _is_visible(self, locator: Locator, timeout: float | None = None) -> bool:
        """Ждёт появления элемента. True — появился, False — не дождались."""
        try:
            self._wait(timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def _is_gone(self, locator: Locator, timeout: float | None = None) -> bool:
        """Ждёт исчезновения элемента. True — исчез, False — так и остался на странице."""
        try:
            self._wait(timeout).until(EC.invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False
