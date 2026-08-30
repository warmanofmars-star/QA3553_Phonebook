import os
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.edge.options import Options

from pages.login_page import LoginPage
from tests.test_login import VALID_PASSWORD, EXISTING_EMAIL


@pytest.fixture
def driver():
    options = Options()

    # Принудительно устанавливаем английский язык для браузера
    options.add_argument('--lang=en-US')
    # Дополнительная настройка преференций (для надежности в Edge/Chrome)
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})

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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Хук, который вызывается после каждой фазы теста (setup, call, teardown).
    Если тест падает, он делает скриншот и прикрепляет его к HTML-отчету.
    """
    outcome = yield
    report = outcome.get_result()

    # Проверяем, что тест упал именно на этапе выполнения (call), а не при настройке
    if report.when == 'call' and report.failed:
        # Пытаемся получить webdriver из фикстур теста (наших driver или authenticated_driver)
        driver = item.funcargs.get('driver') or item.funcargs.get('authenticated_driver')

        if driver:
            # Создаем папку screenshots в корне проекта, если её нет
            screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)

            # Формируем имя скриншота из названия упавшего теста
            test_name = item.name.replace("/", "_").replace("::", "_")
            screenshot_path = os.path.join(screenshots_dir, f"{test_name}.png")

            # Делаем физический скриншот (для истории и pytest-html)
            driver.save_screenshot(screenshot_path)

            # === НОВЫЙ БЛОК ДЛЯ ALLURE ===
            # Прикрепляем скриншот прямо в Allure-отчет в виде байтов
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Скриншот ошибки: {test_name}",
                attachment_type=allure.attachment_type.PNG
            )
            # =============================

            # Прикрепляем скриншот к pytest-html отчету (оставляем как было)
            pytest_html = item.config.pluginmanager.getplugin('html')
            if pytest_html:
                extras = getattr(report, 'extras', [])
                extras.append(pytest_html.extras.image(screenshot_path))
                report.extras = extras