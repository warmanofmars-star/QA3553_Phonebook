import pytest
from selenium import webdriver

from pages.login_page import LoginPage
from tests.test_login import VALID_PASSWORD, EXISTING_EMAIL


@pytest.fixture
def driver():
    driver = webdriver.Edge()
    driver.implicitly_wait(5)
    driver.maximize_window()


    yield driver  # Передаем драйвер в тест
    driver.quit()

@pytest.fixture
def authenticated_driver(driver):
    login_page = LoginPage(driver)
    login_page.open()

    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    # ДОБАВЛЕНО: Ждем, пока авторизация действительно завершится
    login_page.is_logged()

    return driver