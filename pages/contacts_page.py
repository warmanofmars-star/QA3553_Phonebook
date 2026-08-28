from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class ContactListPage(BasePage):
    PAGE_URL = "https://telranedu.web.app/contacts"

    # Локатор кнопки Remove (появляется только когда кликнули на карточку)
    REMOVE_BTN = (By.XPATH, "//button[text()='Remove']")

    def open(self):
        self.driver.get(self.PAGE_URL)

    def _get_contact_locator(self, phone):
        """Вспомогательный метод для получения локатора карточки по номеру телефона"""
        return (By.XPATH, f"//h3[text()='{phone}']")

    def click_contact_by_phone(self, phone):
        """Кликает на карточку контакта в левом списке"""
        locator = self._get_contact_locator(phone)
        self.click(locator)

    def click_remove_button(self):
        """Кликает на кнопку Remove в правой панели"""
        self.click(self.REMOVE_BTN)

    def is_contact_deleted(self, phone):
        """Проверяет, что карточка с указанным телефоном исчезла со страницы"""
        locator = self._get_contact_locator(phone)
        return self.is_disappeared(locator)