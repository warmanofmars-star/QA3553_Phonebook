import os
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from dotenv import load_dotenv
from selenium.webdriver.support.events import EventFiringWebDriver
from utils.listener import PhonebookListener
from api.contact_api import PhonebookAPI

# Загружаем переменные из .env
load_dotenv()

from pages.login_page import LoginPage


@pytest.fixture
def driver():
    # Читаем флаги
    is_headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    is_ci = os.environ.get('CI') == 'true'

    if is_ci:
        # ПРОФЕССИОНАЛЬНЫЙ CI-ПОДХОД: Строго Google Chrome для Linux-сервера (GitHub Actions)
        options = ChromeOptions()
        options.add_argument('--headless=new') # Современный headless для Chrome
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=en-US')
        driver_instance = webdriver.Chrome(options=options)

    else:
        # ЛОКАЛЬНАЯ РАЗРАБОТКА: Каскадный поиск браузера (Chrome -> Edge)
        try:
            # Попытка №1: Пытаемся поднять Chrome, чтобы зеркалировать CI-окружение
            options = ChromeOptions()
            if is_headless:
                options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--lang=en-US')
            driver_instance = webdriver.Chrome(options=options)

        except Exception as e:
            # Попытка №2: Если Chrome нет, делаем мягкий фоллбэк на Edge
            print(f"\n[WARNING] Chrome не запустился. Причина: {e}")
            print("[INFO] Выполняем каскадное переключение на Microsoft Edge...")

            options = EdgeOptions()
            if is_headless:
                options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--lang=en-US')
            driver_instance = webdriver.Edge(options=options)

        if not is_headless:
            driver_instance.maximize_window()

    # Устанавливаем жесткий лимит на загрузку страницы (30 секунд)
    driver_instance.set_page_load_timeout(30)

    # === НАДЕВАЕМ ШПИОНА НА ДРАЙВЕР ПЕРЕД ВЫДАЧЕЙ ===
    decorated_driver = EventFiringWebDriver(driver_instance, PhonebookListener())

    yield decorated_driver  # Передаем ОБЕРНУТЫЙ драйвер в тесты
    decorated_driver.quit()  # В конце убиваем именно обернутый драйвер


@pytest.fixture
def authenticated_driver(driver):
    login_page = LoginPage(driver)
    login_page.open()

    # Берем данные напрямую из .env, не обращаясь к файлу тестов
    login_page.fill_email(os.getenv("USER_EMAIL"))
    login_page.fill_password(os.getenv("USER_PASSWORD"))
    login_page.submit_login()

    # Ждем, пока авторизация действительно завершится
    login_page.is_logged()

    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        driver = item.funcargs.get('driver') or item.funcargs.get('authenticated_driver')

        if driver:
            # ЗАЩИТА: Если перед падением остался висеть алерт, гасим его, чтобы не рушился ChromeDriver
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except Exception:
                pass # Алерта нет, идем дальше спокойно

            test_name = item.name.replace("/", "_").replace("::", "_")
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Скриншот ошибки: {test_name}",
                attachment_type=allure.attachment_type.PNG
            )

@pytest.fixture(scope="session")
def auth_api():
    """Фикстура, которая автоматически создает API-клиента, логинится и возвращает готовую сессию"""
    api = PhonebookAPI()
    email = os.getenv("USER_EMAIL")
    password = os.getenv("USER_PASSWORD")

    with allure.step("Setup Fixture: Автоматическая API-авторизация"):
        response = api.login(email, password)
        assert response.status_code == 200, "КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить API токен!"

    return api

def pytest_make_parametrize_id(val):
    """
    Хук Pytest: запрещает экранировать кириллицу в ID параметризованных тестов.
    """
    return str(val)