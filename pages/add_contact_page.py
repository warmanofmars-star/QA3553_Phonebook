from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from models.contact import Contact
from pages.locators import ContactFormLocators


class ContactPage(BasePage):
    ENDPOINT = "/add"

    ADD_NAV_LINK = (By.CSS_SELECTOR, "a[href='/add']")
    ACTIVE_ADD_NAV_LINK = (By.CSS_SELECTOR, "a[href='/add'].active")  # Активная вкладка
    SAVE_BTN = (By.XPATH, "//button[b[text()='Save']]")

    def fill_contact_form(self, contact: Contact):
        """Оптимизированный метод заполнения формы"""
        for attr_name, locator in ContactFormLocators.FIELDS.items():
            # Достаем значение из объекта Contact (например, contact.name)
            value = getattr(contact, attr_name, None)
            if value is not None:
                self.fill(locator, value)  # Используем метод fill из BasePage


    def is_add_tab_active(self):
        try:
            return self.find(self.ACTIVE_ADD_NAV_LINK).is_displayed()
        except Exception:
            return False


    def submit_contact(self):
        self.click(self.SAVE_BTN)

    def is_contact_card_visible(self, phone):
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        element = WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located(locator)
        )
        return element.is_displayed()