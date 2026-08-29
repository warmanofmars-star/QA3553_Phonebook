import os
import pytest
from selenium import webdriver
from selenium.webdriver.edge.options import Options

from pages.login_page import LoginPage
from tests.test_login import VALID_PASSWORD, EXISTING_EMAIL


@pytest.fixture
def driver():
    options = Options()

    # Проверяем, запускаются ли тесты на сервере GitHub Actions
    if os.environ.get('CI') == 'true':
        options.add_argument('--headless')  # Включаем фоновый режим
        options.add_argument('--no-sandbox')  # Обязательно для Linux-серверов
        options.add_argument('--disable-dev-shm-usage')  # Обход проблемы с памятью на серверах
        options.add_argument('--window-size=1920,1080')  # Задаем размер экрана "вслепую"

    # Передаем опции в драйвер
    driver = webdriver.Edge(options=options)

    # Максимизируем окно только при локальном запуске (с UI)
    if os.environ.get('CI') != 'true':
        driver.maximize_window()

    driver.implicitly_wait(5)

    yield driver  # Передаем драйвер в тест
    driver.quit()


@pytest.fixture
def authenticated_driver(driver):
    login_page = LoginPage(driver)
    login_page.open()

    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    # Ждем, пока авторизация действительно завершится
    login_page.is_logged()

    return driver