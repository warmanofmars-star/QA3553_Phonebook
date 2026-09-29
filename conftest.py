import os
import time
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
    use_selenoid = os.getenv('USE_SELENOID', 'false').lower() == 'true'

    # Переменная для хранения ID сессии Докера
    session_id = None

    if is_ci:
        options = ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=en-US')
        driver_instance = webdriver.Chrome(options=options)

    else:
        if use_selenoid:
            print("\n[INFO] Маршрутизация в изолированный Docker-контейнер (Selenoid)...")
            options = ChromeOptions()
            options.set_capability("browserName", "chrome")
            options.set_capability("browserVersion", "128.0")
            options.set_capability("selenoid:options", {
                "enableVNC": True,
                "enableVideo": True,  # <--- ВКЛЮЧАЕМ ЗАПИСЬ ВИДЕО

            })

            driver_instance = webdriver.Remote(
                command_executor="http://localhost:4444/wd/hub",
                options=options
            )
            # Запоминаем ID сессии, чтобы потом забрать правильное видео
            session_id = driver_instance.session_id

        else:
            try:
                options = ChromeOptions()
                if is_headless:
                    options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--lang=en-US')
                driver_instance = webdriver.Chrome(options=options)

            except Exception as e:
                print(f"\n[WARNING] Chrome не запустился. Причина: {e}")
                options = EdgeOptions()
                if is_headless:
                    options.add_argument('--headless')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--lang=en-US')
                driver_instance = webdriver.Edge(options=options)

    if not is_headless and not use_selenoid:
        driver_instance.maximize_window()
    elif use_selenoid:
        driver_instance.maximize_window()

    driver_instance.set_page_load_timeout(30)
    decorated_driver = EventFiringWebDriver(driver_instance, PhonebookListener())

    yield decorated_driver

    # Закрываем браузер. Только после этой команды Selenoid финализирует mp4 файл!
    decorated_driver.quit()

    # === ИНТЕГРАЦИЯ ВИДЕО В ALLURE ===
    if use_selenoid and session_id:

        # Видео уже физически лежит на твоем диске C, идем прямо за ним
        video_path = rf"C:\selenoid\video\{session_id}.mp4"

        # Умное ожидание: проверяем появление файла на диске (до 10 секунд)
        for attempt in range(10):
            if os.path.exists(video_path):
                # Файл появился. Даем системе 1 секунду, чтобы Докер снял с него блокировку записи
                time.sleep(1)
                try:
                    with open(video_path, "rb") as video_file:
                        allure.attach(
                            video_file.read(),
                            name=f"Видео прохождения теста",
                            attachment_type=allure.attachment_type.MP4
                        )
                    print(f"\n[INFO] Видео успешно прикреплено напрямую с диска Windows!")
                    break  # Успешно прикрепили, выходим из цикла
                except Exception as e:
                    print(f"\n[WARNING] Файл заблокирован, пробуем снова. Ошибка: {e}")

            # Если файла еще нет, ждем 1 секунду перед новой проверкой
            time.sleep(1)

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