from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:
    LOGIN_NAV_LINK = (By.CSS_SELECTOR, "[href='/login']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='email']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    LOGIN_BTN = (By.XPATH, "//button[text()='Login']")

    # Локатор для кнопки регистрации (по атрибуту name)
    REGISTRATION_BTN = (By.CSS_SELECTOR, "button[name='registration']")
    SIGN_OUT_BTN = (By.XPATH, "//*[text()='Sign Out']")

    # Новый локатор для сообщения "Registration failed with code 409"
    ERROR_MESSAGE_DIV = (By.XPATH, "//div[contains(@style, 'color: red')]")

    def __init__(self, driver):
        self.driver = driver

    def open_login_form(self):
        self.driver.find_element(*self.LOGIN_NAV_LINK).click()

    def fill_password(self, password):
        self.driver.find_element(*self.PASSWORD_INPUT).clear()
        self.driver.find_element(*self.PASSWORD_INPUT).send_keys(password)

    def fill_email(self, email):
        self.driver.find_element(*self.EMAIL_INPUT).clear()
        self.driver.find_element(*self.EMAIL_INPUT).send_keys(email)

    def submit_login(self):
        self.driver.find_element(*self.LOGIN_BTN).click()

    def submit_registration(self):
        self.driver.find_element(*self.REGISTRATION_BTN).click()

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

    # Новый метод для чтения красного текста ошибки со страницы
    def get_error_message_text(self):
        error_element = WebDriverWait(self.driver, timeout=5).until(
            EC.visibility_of_element_located(self.ERROR_MESSAGE_DIV)
        )
        return error_element.text
