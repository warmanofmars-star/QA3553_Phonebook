import allure
import pytest
from playwright.sync_api import Page
from pages.pw_login_page import PwLoginPage


@pytest.mark.smoke
@pytest.mark.playwright
@allure.epic("Playwright Testing")
@allure.feature("Login")
@allure.story("Positive Login (Playwright + POM)")
@allure.severity(allure.severity_level.BLOCKER)
def test_pw_login_success(page: Page, temp_user):
    pw_login_page = PwLoginPage(page)
    user = temp_user.user

    pw_login_page.open()
    pw_login_page.login(user.email, user.password)

    pw_login_page.check_sign_out_visible()