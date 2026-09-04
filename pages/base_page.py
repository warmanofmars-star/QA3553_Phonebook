import os
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

class BasePage:
    BASE_URL = os.getenv("BASE_URL")
    ENDPOINT = ""
    DEFAULT_TIMEOUT = 5

    def __init__(self, driver):
        self.driver = driver
        # Подключаем наш логгер с пометкой UI
        self.logger = get_logger("UI")

    def open(self):
        url = f"{self.BASE_URL}{self.ENDPOINT}"
        self.logger.info(f"Открываем страницу: {url}")
        self.driver.get(url)

    def find(self, locator):
        # Исключительно для отладки, обычно поиск элемента не логируют, чтобы не засорять эфир,
        # но мы оставим, чтобы видеть каждый шаг.
        self.logger.info(f"Ищем элемент: {locator}")
        return self.driver.find_element(*locator)

    def click(self, locator):
        self.logger.info(f"Клик по элементу: {locator}")
        self.find(locator).click()

    def fill(self, locator, value):
        self.logger.info(f"Ввод данных в поле: {locator}")
        self.find(locator).clear()
        self.find(locator).send_keys(value)

    # ==========================================
    # ОБЩИЕ ЭЛЕМЕНТЫ НАВИГАЦИИ (HEADER)
    # ==========================================
    SIGN_OUT_BTN = (By.XPATH, "//button[text()='Sign Out']")

    def click_sign_out_button(self):
        self.logger.info("Нажимаем кнопку 'Sign Out'")
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(self.SIGN_OUT_BTN)
        )
        element.click()

    # ==========================================
    # УНИВЕРСАЛЬНЫЕ МЕТОДЫ (ALERTS & WAITS)
    # ==========================================
    def get_alert_text(self):
        self.logger.info("Ожидаем появления Alert и читаем его текст")
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        text = alert.text
        self.logger.info(f"Прочитан текст Alert: '{text}'")
        return text

    def accept_alert(self):
        self.logger.info("Подтверждаем (Accept) Alert")
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert.accept()

    def is_disappeared(self, locator):
        self.logger.info(f"Ожидаем исчезновения элемента: {locator}")
        try:
            WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.invisibility_of_element_located(locator)
            )
            self.logger.info("Элемент успешно исчез со страницы")
            return True
        except TimeoutException:
            # Используем warning, чтобы сообщение подсветилось желтым
            self.logger.warning(f"Элемент НЕ исчез в течение {self.DEFAULT_TIMEOUT} секунд!")
            return False