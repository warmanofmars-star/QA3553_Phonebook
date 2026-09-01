import os
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

from pages.login_page import LoginPage


@pytest.fixture
def driver():
    options = Options()

    # Принудительно устанавливаем английский язык для браузера
    options.add_argument('--lang=en-US')
    # Дополнительная настройка преференций (для надежности в Edge/Chrome)
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    # Читаем наш флаг из .env
    is_headless = os.getenv('HEADLESS_MODE') == 'true'

    # Включаем Headless, если мы на GitHub Actions (CI) ИЛИ если включили флаг локально
    if os.environ.get('CI') == 'true' or is_headless:
        options.add_argument('--disable-gpu') # Отключение видеокарты
        options.add_argument('--headless')  # Включаем фоновый режим
        options.add_argument('--no-sandbox')  # Обязательно для Linux-серверов
        options.add_argument('--disable-dev-shm-usage')  # Обход проблемы с памятью на серверах
        options.add_argument('--window-size=1920,1080')  # Задаем размер экрана "вслепую"

    # Передаем опции в драйвер
    driver = webdriver.Edge(options=options)

    # Максимизируем окно только если Headless выключен
    if not (os.environ.get('CI') == 'true' or is_headless):
        driver.maximize_window()

    # Устанавливаем жесткий лимит на загрузку страницы (30 секунд)
    driver.set_page_load_timeout(30)

    yield driver  # Передаем драйвер в тест
    driver.quit()


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