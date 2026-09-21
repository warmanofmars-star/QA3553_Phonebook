import allure
from playwright.sync_api import Page, expect
from pages.pw_base_page import PwBasePage


class PwLoginPage(PwBasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.endpoint = "/login"

        # --- ЛОКАТОРЫ PLAYWRIGHT ---
        self.email_input = page.locator("input[name='email']")
        self.password_input = page.locator("input[name='password']")
        self.login_btn = page.locator("button", has_text="Login")
        self.sign_out_btn = page.locator("button", has_text="Sign Out")

    # --- ДЕЙСТВИЯ ---
    def open(self):
        self.open_url(self.endpoint)

    def fill_email(self, email: str):
        # Используем наш умный метод fill из PwBasePage
        self.fill(self.email_input, email)

    def fill_password(self, password: str):
        # Передаем флаг is_secret, и пароль замаскируется и в логах, и в Allure!
        self.fill(self.password_input, password, is_secret=True)

    def submit_login(self):
        # Передаем имя элемента для красивых логов
        self.click(self.login_btn, "Login")

    def login(self, email, password):
        self.fill_email(email)
        self.fill_password(password)
        self.submit_login()

    # --- ПРОВЕРКИ (ASSERTS) ---
    def check_sign_out_visible(self):
        self.logger.info("Проверка: Ожидаем появление кнопки Sign Out...")

        with allure.step("Проверка успешной авторизации (появление кнопки Sign Out)"):
            expect(self.sign_out_btn).to_be_visible(timeout=self.expect_timeout)

        self.logger.info("Проверка пройдена: кнопка Sign Out появилась!")