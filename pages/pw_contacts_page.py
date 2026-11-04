"""Список контактов, карточка и форма редактирования — Playwright (минимум для тестов сбоев)."""

from playwright.sync_api import Page, expect

from models.contact import Contact
from pages.pw_base_page import PwBasePage
from utils.allure_steps import step


class PwContactsPage(PwBasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.endpoint = "/contacts"
        self._cards = page.locator("[class^='contact-item_card__']")
        self._details = page.locator("[class^='contact-item-detailed_card__']")
        self._loading = page.get_by_text("Loading...", exact=True)
        self._empty = page.get_by_text("No Contacts here!")
        self._edit_btn = page.locator("button:text-is('Edit')")
        self._remove_btn = page.locator("button:text-is('Remove')")
        self._save_edit_btn = page.locator("button:text-is('Save')")
        self._edit_name = page.locator("input[placeholder='Name']")

    def _card(self, phone: str):
        return self._cards.filter(has=self.page.locator(f"h3:text-is('{phone}')"))

    # --- ДЕЙСТВИЯ ---
    @step("Дождаться перехода на страницу контактов")
    def wait_opened(self) -> None:
        self.page.wait_for_url(f"**{self.endpoint}", timeout=self.expect_timeout)

    @step("Открыть карточку контакта {phone}")
    def open_details(self, phone: str) -> None:
        self._card(phone).click()
        expect(self._details).to_be_visible(timeout=self.expect_timeout)

    @step("Изменить имя контакта на '{new_name}' и нажать Save")
    def edit_name(self, new_name: str) -> None:
        self._edit_btn.click()
        self._edit_name.fill(new_name)
        self._save_edit_btn.click()

    @step("Нажать Remove в карточке контакта")
    def remove(self) -> None:
        self._remove_btn.click()

    # --- СОСТОЯНИЕ ---
    def card_name(self, phone: str) -> str | None:
        """Имя на компактной карточке контакта; None — карточки нет."""
        card = self._card(phone)
        return card.locator("h2").inner_text().strip() if card.count() else None

    def card_shown(self, phone: str) -> bool:
        return self._card(phone).count() > 0

    def is_edit_form_open(self) -> bool:
        return self._edit_name.is_visible()

    def edit_name_value(self) -> str | None:
        return self._edit_name.input_value() if self.is_edit_form_open() else None

    def loading_shown(self) -> bool:
        return self._loading.is_visible()

    def loading_gone_within(self, timeout_ms: int) -> bool:
        """Исчез ли индикатор загрузки за timeout_ms (не бросает исключений — для проверок)."""
        return self.wait_until(lambda: not self.loading_shown(), timeout_ms)

    def redirected_to_login_within(self, timeout_ms: int) -> bool:
        """Перешло ли приложение на страницу входа за timeout_ms."""
        return self.wait_until(lambda: "/login" in self.page.url, timeout_ms)

    # --- ПРОВЕРКИ ---
    @step("Проверить: виден индикатор загрузки")
    def check_loading_visible(self) -> None:
        expect(self._loading).to_be_visible(timeout=self.expect_timeout)

    @step("Проверить: видна карточка контакта {contact.phone}")
    def check_card_visible(self, contact: Contact) -> None:
        expect(self._card(contact.phone)).to_be_visible(timeout=self.expect_timeout)

    @step("Проверить: видно сообщение о пустом списке")
    def check_empty_message_visible(self) -> None:
        expect(self._empty).to_be_visible(timeout=self.expect_timeout)
