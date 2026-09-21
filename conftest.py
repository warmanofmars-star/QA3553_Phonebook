import os
import pytest
import allure
import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from dotenv import load_dotenv
from selenium.webdriver.support.events import EventFiringWebDriver
from utils.listener import PhonebookListener

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
        driver_instance = webdriver.Chrome(options=options)

    else:
        # ЛОКАЛЬНАЯ РАЗРАБОТКА: Каскадный поиск браузера (Chrome -> Edge)
        try:
            # Попытка №1: Пытаемся поднять Chrome, чтобы зеркалировать CI-окружение
            options = ChromeOptions()
            if is_headless:
                options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            driver_instance = webdriver.Chrome(options=options)

        except Exception as e:
            # Попытка №2: Если Chrome нет, делаем мягкий фоллбэк на Edge
            print(f"\n[WARNING] Chrome не запустился. Причина: {e}")
            print("[INFO] Выполняем каскадное переключение на Microsoft Edge...")

            options = EdgeOptions()
            if is_headless:
                options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
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
    """
    Хук, который вызывается после каждой фазы теста (setup, call, teardown).
    Если тест падает, он делает скриншот экрана и прикрепляет его к Allure-отчету.
    """
    outcome = yield
    report = outcome.get_result()

    # Проверяем, что тест упал именно на этапе выполнения (call), а не при настройке
    if report.when == 'call' and report.failed:
        # Пытаемся получить webdriver из фикстур теста
        driver = item.funcargs.get('driver') or item.funcargs.get('authenticated_driver')

        if driver:
            # Формируем читаемое имя для скриншота из названия теста
            test_name = item.name.replace("/", "_").replace("::", "_")

            # Прикрепляем скриншот напрямую в Allure (без сохранения на жесткий диск)
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Скриншот ошибки: {test_name}",
                attachment_type=allure.attachment_type.PNG
            )

#здесь мы получим токен авторизации для API-тестов и будем вызывать его
@pytest.fixture(scope="session")
def api_token():
    """Получает токен авторизации один раз для всех API-тестов"""
    api_url = os.getenv("API_URL")

    login_payload = {
        "username": os.getenv("USER_EMAIL"),
        "password": os.getenv("USER_PASSWORD")
    }

    response = requests.post(f"{api_url}/v1/user/login/usernamepassword", json=login_payload)

    # Жесткая проверка, чтобы тесты даже не начинались, если бэкенд лежит
    assert response.status_code == 200, "КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить API токен!"

    # Возвращаем сам токен (строку)
    return response.json().get("token")

def pytest_make_parametrize_id(val):
    """
    Хук Pytest: запрещает экранировать кириллицу в ID параметризованных тестов.
    """
    return str(val)