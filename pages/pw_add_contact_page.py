"""Форма добавления контакта — Playwright (минимум для тестов сбоев)."""

from playwright.sync_api import Page

from models.contact import Contact
from pages.pw_base_page import PwBasePage
from utils.allure_steps import step

# Поле модели Contact -> placeholder поля формы.
# *= (содержит) для описания: на странице добавления placeholder 'description'
FIELDS = {
    "name": "input[placeholder='Name']",
    "last_name": "input[placeholder='Last Name']",
    "phone": "input[placeholder='Phone']",
    "email": "input[placeholder='email']",
    "address": "input[placeholder='Address']",
    "description": "input[placeholder*='desc']",
}


class PwAddContactPage(PwBasePage):
    FIELD_NAMES = tuple(FIELDS)

    def __init__(self, page: Page):
        super().__init__(page)
        self._add_link = page.locator("a[href='/add']")
        self._save_btn = page.locator("button:has(b:text-is('Save'))")

    @step("Открыть форму добавления через меню ADD")
    def open_from_menu(self) -> None:
        # Через меню, а не goto: переход внутри приложения не перезагружает страницу
        self._add_link.click()
        self.page.locator(FIELDS["name"]).wait_for(timeout=self.expect_timeout)

    @step("Заполнить форму добавления контакта {contact.phone}")
    def fill_form(self, contact: Contact) -> None:
        for field, selector in FIELDS.items():
            self.page.locator(selector).fill(getattr(contact, field))

    @step("Нажать Save")
    def save(self) -> None:
        self._save_btn.click()

    @step("Дважды кликнуть по Save")
    def double_click_save(self) -> None:
        self._save_btn.dblclick()

    def form_values(self) -> dict[str, str]:
        """Текущие значения полей формы (пустой словарь — формы на странице нет)."""
        if not self.page.locator(FIELDS["name"]).is_visible():
            return {}
        return {field: self.page.locator(selector).input_value() for field, selector in FIELDS.items()}
