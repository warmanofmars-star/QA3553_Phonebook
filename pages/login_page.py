from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.allure_steps import step


class LoginPage(BasePage):
    ENDPOINT = "/login"
    PAGE_NAME = "Вход и регистрация"

    _EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='email']")
    _PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    _LOGIN_BTN = (By.CSS_SELECTOR, "button[name='login']")
    _REGISTRATION_BTN = (By.CSS_SELECTOR, "button[name='registration']")

    @step("Войти как {email}")
    def login(self, email: str, password: str) -> None:
        # Пароль не попадает ни в название шага, ни в его параметры (см. utils/allure_steps.py)
        self._fill_credentials(email, password)
        self._click(self._LOGIN_BTN)

    @step("Зарегистрироваться как {email}")
    def register(self, email: str, password: str) -> None:
        self._fill_credentials(email, password)
        self._click(self._REGISTRATION_BTN)

    def is_login_form_displayed(self, timeout: float | None = None) -> bool:
        """Форма входа на экране — например, после выхода или редиректа анонима."""
        return self._is_visible(self._LOGIN_BTN, timeout)

    def _fill_credentials(self, email: str, password: str) -> None:
        self._fill(self._EMAIL_INPUT, email)
        self._fill(self._PASSWORD_INPUT, password)
