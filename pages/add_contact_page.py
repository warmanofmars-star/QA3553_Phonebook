from selenium.webdriver.common.by import By

from models.contact import Contact
from pages.base_page import BasePage
from pages.locators import ContactFormLocators
from utils.allure_steps import step


class AddContactPage(BasePage):
    ENDPOINT = "/add"
    PAGE_NAME = "Добавление контакта"

    _ACTIVE_ADD_TAB = (By.CSS_SELECTOR, "a[href='/add'].active")
    _SAVE_BTN = (By.XPATH, "//button[b[text()='Save']]")

    @step("Заполнить форму контакта (телефон {contact.phone})")
    def fill_form(self, contact: Contact) -> None:
        """Заполняет поля, у которых в contact задано значение (None — поле не трогаем)."""
        for field, locator in ContactFormLocators.FIELDS.items():
            value = getattr(contact, field)
            if value is not None:
                self._fill(locator, value)

    @step("Нажать Save")
    def save(self) -> None:
        self._click(self._SAVE_BTN)

    def add_contact(self, contact: Contact) -> None:
        """Заполнить форму и сохранить — короткий путь для типового сценария."""
        self.fill_form(contact)
        self.save()

    def is_add_tab_active(self) -> bool:
        """Пользователь всё ещё на вкладке ADD (например, после ошибки валидации)."""
        return self._is_visible(self._ACTIVE_ADD_TAB)
