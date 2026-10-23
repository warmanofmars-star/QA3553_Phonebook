import os
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from utils.logger import get_logger
from selenium.webdriver.remote.webelement import WebElement

load_dotenv()


class BasePage:
    BASE_URL = os.getenv("BASE_URL", "https://telranedu.web.app")
    ENDPOINT = ""
    DEFAULT_TIMEOUT = 5

    def __init__(self, driver):
        self.driver = driver
        self.logger = get_logger("UI")

    @allure.step("Открытие страницы")
    def open(self):
        url = f"{self.BASE_URL}{self.ENDPOINT}"
        self.logger.info(f"Открываем страницу: {url}")
        self.driver.get(url)

    @allure.step("Поиск элемента: {locator}")
    def find(self, locator: tuple[str, str]) -> WebElement:
        return WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(locator)
        )

    @allure.step("Клик по элементу: {locator}")
    def click(self, locator: tuple[str, str]) -> None:
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()

    def fill(self, locator, value, is_secret=False):
        """
        Вводит текст в поле с предварительным ожиданием видимости.
        Если is_secret=True, пароль в отчетах Allure будет заменен на звездочки.
        """
        display_value = "********" if is_secret else value

        with allure.step(f"Ввод текста '{display_value}' в поле {locator}"):
            element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.visibility_of_element_located(locator)
            )
            element.clear()
            element.send_keys(value)

    @allure.step("Снятие фокуса с элемента (клик по фону)")
    def remove_focus(self):
        self.click((By.CSS_SELECTOR, "body"))

    # ==========================================
    # ОБЩИЕ ЭЛЕМЕНТЫ НАВИГАЦИИ (HEADER)
    # ==========================================
    SIGN_OUT_BTN = (By.XPATH, "//button[text()='Sign Out']")

    @allure.step("Нажатие кнопки 'Sign Out'")
    def click_sign_out_button(self):
        self.logger.info("Нажимаем кнопку 'Sign Out'")
        self.click(self.SIGN_OUT_BTN)

    # ==========================================
    # УНИВЕРСАЛЬНЫЕ МЕТОДЫ (ALERTS & WAITS)
    # ==========================================
    @allure.step("Чтение текста Alert")
    def get_alert_text(self):
        self.logger.info("Ожидаем появления Alert и читаем его текст")
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        text = alert.text
        self.logger.info(f"Прочитан текст Alert: '{text}'")
        return text

    @allure.step("Подтверждение (Accept) Alert")
    def accept_alert(self):
        self.logger.info("Подтверждаем (Accept) Alert")
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert.accept()

    @allure.step("Ожидание исчезновения элемента: {locator}")
    def is_disappeared(self, locator):
        self.logger.info(f"Ожидаем исчезновения элемента: {locator}")
        try:
            WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.invisibility_of_element_located(locator)
            )
            self.logger.info("Элемент успешно исчез со страницы")
            return True
        except TimeoutException:
            self.logger.warning(f"Элемент НЕ исчез в течение {self.DEFAULT_TIMEOUT} секунд!")
            return False