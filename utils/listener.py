from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.common.exceptions import WebDriverException, NoSuchElementException  # <-- Добавили точечный импорт
from utils.logger import get_logger

class PhonebookListener(AbstractEventListener):
    def __init__(self):
        # Подключаем наш фирменный логгер с пометкой UI
        self.logger = get_logger("UI")

    def before_navigate_to(self, url, driver):
        self.logger.info(f"Переход по ссылке: {url}")

    def before_find(self, by, value, driver):
        # Логируем поиск элементов
        self.logger.info(f"Поиск элемента -> By: {by}, Value: '{value}'")

    def before_click(self, element, driver):
        # Пытаемся достать текст кнопки или ссылки, по которой кликаем, для красоты логов
        try:
            element_text = element.text
            tag_name = element.tag_name
            self.logger.info(f"Клик по элементу <{tag_name}> с текстом: '{element_text}'")
        except WebDriverException:  # <-- Теперь ловим только ошибки Selenium!
            self.logger.info("Клик по элементу (текст недоступен)")

    def before_change_value_of(self, element, driver):
        self.logger.info("Ввод данных в поле формы...")

    def on_exception(self, exception, driver):
        # Игнорируем штатные ошибки поиска, которые возникают во время работы WebDriverWait
        if isinstance(exception, NoSuchElementException):
            return

        # Все остальные реальные ошибки логируем красным
        self.logger.error(f"ПЕРЕХВАТ ОШИБКИ WEBDRIVER: {exception}")