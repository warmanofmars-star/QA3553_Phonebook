import os
import allure
from playwright.sync_api import Page
from pages.pw_login_page import PwLoginPage

VALID_EMAIL = os.getenv("USER_EMAIL")
VALID_PASSWORD = os.getenv("USER_PASSWORD")

@allure.epic("Playwright Testing")
@allure.feature("Login")
@allure.story("Positive Login (Playwright + POM)")
@allure.severity(allure.severity_level.BLOCKER)
def test_pw_login_success(page: Page): # <--- Берем встроенную фикстуру page
    # 1. Инициализируем Page Object
    pw_login_page = PwLoginPage(page)

    # 2. Открываем страницу и логинимся
    pw_login_page.open()
    pw_login_page.login(VALID_EMAIL, VALID_PASSWORD)

    # 3. Проверяем результат встроенным expect()
    pw_login_page.check_sign_out_visible()