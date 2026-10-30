from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener

from utils.logger import get_logger


class PhonebookListener(AbstractEventListener):
    """Логирует низкоуровневые действия WebDriver.

    Всё пишется уровнем DEBUG: в отчёт и консоль это не попадает (там уровень INFO
    и понятные шаги из @step), но остаётся в файле logs/*.log для глубокой отладки.
    """

    def __init__(self):
        self.logger = get_logger("WEBDRIVER")

    def before_navigate_to(self, url, driver):
        self.logger.debug(f"Переход по ссылке: {url}")

    def before_find(self, by, value, driver):
        self.logger.debug(f"Поиск элемента -> {by}: {value}")

    def before_click(self, element, driver):
        try:
            text = element.text.replace("\n", " ").strip()
            if len(text) > 50:
                text = text[:47] + "..."
            self.logger.debug(f"Клик по <{element.tag_name}> с текстом '{text}'")
        except WebDriverException:
            self.logger.debug("Клик по элементу (текст недоступен)")

    def before_change_value_of(self, element, driver):
        self.logger.debug("Ввод данных в поле формы")  # значение не пишем: там может быть пароль

    def on_exception(self, exception, driver):
        # Исключения внутри ожиданий (нет элемента, нет алерта...) — штатная часть
        # поллинга WebDriverWait, а не ошибка теста. Настоящие ошибки покажет pytest.
        if isinstance(exception, NoSuchElementException):
            return
        self.logger.debug(f"Исключение WebDriver: {type(exception).__name__}: {exception}".splitlines()[0])
