from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from models.contact import Contact


class ContactPage(BasePage):
    PAGE_URL = "https://telranedu.web.app/add"

    ADD_NAV_LINK = (By.CSS_SELECTOR, "a[href='/add']")
    ACTIVE_ADD_NAV_LINK = (By.CSS_SELECTOR, "a[href='/add'].active")  # Активная вкладка

    NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder='Name']")
    LAST_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder='Last Name']")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder='Phone']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[placeholder='email']")
    ADDRESS_INPUT = (By.CSS_SELECTOR, "input[placeholder='Address']")
    DESCRIPTION_INPUT = (By.CSS_SELECTOR, "input[placeholder='description']")
    SAVE_BTN = (By.XPATH, "//button[b[text()='Save']]")

    def open(self):
        self.driver.get(self.PAGE_URL)

    def is_add_tab_active(self):
        try:
            return self.find(self.ACTIVE_ADD_NAV_LINK).is_displayed()
        except Exception:
            return False

    def fill_name(self, name):
        self.fill(self.NAME_INPUT, name)

    def fill_last_name(self, last_name):
        self.fill(self.LAST_NAME_INPUT, last_name)

    def fill_phone(self, phone):
        self.fill(self.PHONE_INPUT, phone)

    def fill_email(self, email):
        self.fill(self.EMAIL_INPUT, email)

    def fill_address(self, address):
        self.fill(self.ADDRESS_INPUT, address)

    def fill_description(self, description):
        self.fill(self.DESCRIPTION_INPUT, description)

    def fill_contact_form(self, contact: Contact):
        self.fill_name(contact.name)
        self.fill_last_name(contact.last_name)
        self.fill_phone(contact.phone)
        self.fill_email(contact.email)
        self.fill_address(contact.address)
        self.fill_description(contact.description)

    def submit_contact(self):
        self.click(self.SAVE_BTN)

    def is_contact_card_visible(self, phone):
        locator = (By.XPATH, f"//h3[text()='{phone}']")
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(locator)
        )
        return element.is_displayed()