from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from models.contact import Contact
from pages.base_page import BasePage
from pages.locators import ContactFormLocators
from utils.allure_steps import step


class ContactsPage(BasePage):
    ENDPOINT = "/contacts"
    PAGE_NAME = "Список контактов"

    # Приложение использует CSS Modules: классы вида contact-item_card__2SOIM, где
    # суффикс — хэш, который меняется при пересборке фронтенда. Поэтому ищем по
    # стабильному началу класса (^= — "начинается с"), а не по полному имени.
    # В реальной команде правильнее попросить разработчиков добавить data-testid.
    _CARD = (By.CSS_SELECTOR, "[class^='contact-item_card__']")
    _DETAILS = (By.CSS_SELECTOR, "[class^='contact-item-detailed_card__']")

    _EDIT_BTN = (By.XPATH, "//button[text()='Edit']")
    _REMOVE_BTN = (By.XPATH, "//button[text()='Remove']")
    _SAVE_EDIT_BTN = (By.XPATH, "//button[text()='Save']")

    @staticmethod
    def _card_by_phone(phone: str):
        """Карточка в списке слева, найденная по телефону (h3 внутри карточки)."""
        return By.XPATH, f"//div[starts-with(@class, 'contact-item_card__')][h3[text()='{phone}']]"

    # ==========================================
    # Список
    # ==========================================
    def is_card_displayed(self, phone: str, timeout: float | None = None) -> bool:
        """Ждёт появления карточки с телефоном. False — так и не появилась."""
        return self._is_visible(self._card_by_phone(phone), timeout)

    def is_card_gone(self, phone: str, timeout: float | None = None) -> bool:
        """Ждёт исчезновения карточки с телефоном. False — так и осталась в списке."""
        return self._is_gone(self._card_by_phone(phone), timeout)

    def cards_count(self) -> int:
        """Сколько карточек в списке прямо сейчас."""
        return self._count(self._CARD)

    @step("Открыть карточку контакта {phone}")
    def open_details(self, phone: str) -> None:
        self._click(self._card_by_phone(phone))

    def details_text(self) -> str:
        """Весь текст правой панели с деталями контакта."""
        return self._find_visible(self._DETAILS).text

    # ==========================================
    # Удаление
    # ==========================================
    @step("Удалить контакт {phone}")
    def delete_contact(self, phone: str) -> None:
        """Открывает карточку и нажимает Remove. Исчезновение карточки проверяет тест."""
        self.open_details(phone)
        self._click(self._REMOVE_BTN)

    @step("Удалить все контакты по одному")
    def delete_all_contacts(self) -> None:
        """Удаляет контакты, всегда кликая по первой карточке.

        После каждого удаления React перерисовывает список, поэтому карточки ищем
        заново на каждой итерации (иначе StaleElementReferenceException).
        Лимит итераций защищает от бесконечного цикла, если удаление сломано.
        """
        max_iterations = self.cards_count() + 5
        for _ in range(max_iterations):
            count_before = self.cards_count()
            if count_before == 0:
                return
            self.driver.find_elements(*self._CARD)[0].click()
            self._click(self._REMOVE_BTN)
            self._wait().until(lambda driver: self.cards_count() < count_before)
        raise AssertionError(f"Не удалось удалить все контакты за {max_iterations} попыток")

    # ==========================================
    # Редактирование
    # ==========================================
    @step("Нажать Edit")
    def start_editing(self) -> None:
        self._click(self._EDIT_BTN)

    @step("Изменить поля формы редактирования")
    def fill_edit_form(self, contact: Contact) -> None:
        """Меняет поля, у которых в contact задано значение (None — поле не трогаем).
        Пустая строка "" очищает поле."""
        for field, locator in ContactFormLocators.FIELDS.items():
            value = getattr(contact, field)
            if value is not None:
                self._replace_text(locator, value)

    @step("Нажать Save в форме редактирования")
    def save_edit(self) -> None:
        self._click(self._SAVE_EDIT_BTN)

    def edit_contact(self, phone: str, changes: Contact) -> None:
        """Полный сценарий редактирования: открыть карточку, Edit, изменить поля, Save."""
        self.open_details(phone)
        self.start_editing()
        self.fill_edit_form(changes)
        self.save_edit()

    def _replace_text(self, locator, text: str) -> None:
        """Надёжная замена текста в поле React-формы.

        element.clear() в React-формах ненадёжен: поле визуально очищается, но
        состояние компонента не обновляется. Выделение всего текста + Backspace
        имитирует действия пользователя и корректно запускает обработчики React.
        """
        element = self._wait().until(EC.element_to_be_clickable(locator))
        # Сочетание "выделить всё" зависит от ОС, на которой запущен БРАУЗЕР, а не тесты:
        # с Mac через Selenoid браузер работает в Linux-контейнере и ждёт Ctrl, а не Cmd
        browser_os = str(self.driver.capabilities.get("platformName", "")).lower()
        select_all = Keys.COMMAND if "mac" in browser_os else Keys.CONTROL
        element.send_keys(select_all + "a")
        element.send_keys(Keys.BACKSPACE)
        if text:
            element.send_keys(text)
