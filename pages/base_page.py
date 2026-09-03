import os
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv  # <--- Добавляем импорт

# Загружаем переменные из .env сразу при чтении этого файла
load_dotenv()

class BasePage:
    # Базовый URL берем из .env
    BASE_URL = os.getenv("BASE_URL")
    # Эндпоинт по умолчанию пустой (переопределим в наследниках)
    ENDPOINT = ""

    DEFAULT_TIMEOUT = 5

    def __init__(self, driver):
        self.driver = driver

    def open(self):
        """Универсальный метод открытия страницы"""
        # Склеиваем корень сайта и конкретный эндпоинт страницы
        self.driver.get(f"{self.BASE_URL}{self.ENDPOINT}")

    def find(self, locator):
        return self.driver.find_element(*locator)

    def click(self, locator):
        self.find(locator).click()

    def fill(self, locator, value):
        self.find(locator).clear()
        self.find(locator).send_keys(value)

    # ==========================================
    # ОБЩИЕ ЭЛЕМЕНТЫ НАВИГАЦИИ (HEADER)
    # ==========================================
    SIGN_OUT_BTN = (By.XPATH, "//button[text()='Sign Out']")

    def click_sign_out_button(self):
        """Кликает по кнопке Sign Out в верхнем общем меню (доступно с любой страницы)"""
        # Ждем, пока кнопка появится и станет кликабельной, затем кликаем
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(EC.element_to_be_clickable(self.SIGN_OUT_BTN))
        element.click()

    # Универсальные методы работы с алертами для всех страниц
    def get_alert_text(self):
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        return alert.text

    def accept_alert(self):
        alert = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert.accept()

    def is_disappeared(self, locator):
        """Ждет, пока элемент не исчезнет со страницы. Возвращает True, если исчез."""
        try:
            WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False