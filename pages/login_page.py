from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

class LoginPage(BasePage):
    PAGE_URL = "https://telranedu.web.app/login"

    LOGIN_NAV_LINK = (By.CSS_SELECTOR, "[href='/login']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    LOGIN_BTN = (By.XPATH, "//button[text()='Login']")
    REGISTRATION_BTN = (By.CSS_SELECTOR, "button[name='registration']")
    SIGN_OUT_BTN = (By.XPATH, "//*[text()='Sign Out']")

    def open(self):
        self.driver.get(self.PAGE_URL)

    def open_login_form(self):
        self.click(self.LOGIN_NAV_LINK) # Используем метод click из BasePage

    def fill_password(self, password):
        self.fill(self.PASSWORD_INPUT, password) # Используем метод fill из BasePage

    def fill_email(self, email):
        self.fill(self.EMAIL_INPUT, email) # Убрали лишний self, добавили self. к локатору

    def submit_login(self):
        self.click(self.LOGIN_BTN)

    def submit_registration(self):
        self.click(self.REGISTRATION_BTN)

    def is_logged(self):
        try:
            WebDriverWait(self.driver, timeout=5).until(
                EC.visibility_of_element_located(self.SIGN_OUT_BTN)
            )
            return True
        except TimeoutError:
            return False

    def get_alert_text(self):
        alert = WebDriverWait(self.driver, timeout=5).until(
            EC.alert_is_present()
        )
        return alert.text

    def accept_alert(self):
        self.driver.switch_to.alert.accept()