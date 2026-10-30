"""
Общие фикстуры и хуки pytest для всего проекта.

Разделы:
  1. Параметры командной строки
  2. Пользователи и API (sandbox: свой пользователь на каждый тест)
  3. Тестовые данные (контакты, созданные через API)
  4. Браузер Selenium
  5. Браузер Playwright
  6. Хуки отчётности

Как устроены зависимости фикстур (стрелка = "использует"):

    authenticated_driver ──> driver
              │
              └──────────> temp_user <── auth_api <── create_contact <── created_contact

Фикстуры по умолчанию живут в пределах одного теста. Поэтому если тест просит
и authenticated_driver, и created_contact, оба получат ОДНОГО и того же
temp_user: контакт создаётся именно у того пользователя, под которым залогинен браузер.
"""

import logging
import os
import platform
import time
from dataclasses import dataclass, replace
from pathlib import Path

import allure
import pytest
from selenium.webdriver.support.events import EventFiringWebDriver

from api.contact_api import PhonebookAPI
from config import PROJECT_ROOT, settings
from data.data_generator import ContactGenerator, UserGenerator
from drivers.factory import SUPPORTED_BROWSERS, attach_selenoid_video, create_driver
from models.contact import Contact
from models.user import User
from pages.login_page import LoginPage
from utils.listener import PhonebookListener
from utils.preconditions import require


# ==========================================
# 1. ПАРАМЕТРЫ КОМАНДНОЙ СТРОКИ И НАСТРОЙКА ЛОГОВ
# ==========================================
LOG_DIR = PROJECT_ROOT / "logs"

# Сторонние библиотеки на уровне INFO/DEBUG пишут много служебного шума
NOISY_LOGGERS = ("urllib3", "selenium", "faker", "asyncio")


def pytest_configure(config):
    """Настраивает файл логов для текущего процесса pytest.

    Проблема: при запуске с xdist (-n 4) тесты выполняют несколько процессов-воркеров.
    Если все они пишут в ОДИН файл, они затирают друг друга. Поэтому:
      * обычный запуск             -> logs/pytest.log
      * воркер xdist (gw0, gw1...) -> logs/pytest_gw0.log, logs/pytest_gw1.log, ...
      * главный процесс xdist      -> файла нет: сам он тесты не выполняет
    Явно переданный --log-file из командной строки имеет приоритет.
    """
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    worker_id = os.environ.get("PYTEST_XDIST_WORKER")  # есть только внутри воркера xdist
    is_xdist_controller = worker_id is None and config.getoption("numprocesses", default=None)

    if worker_id is None:
        # Главный процесс (или обычный запуск) стартует раньше воркеров:
        # чистим файлы прошлого прогона, чтобы не путаться в старых pytest_gw*.log
        LOG_DIR.mkdir(exist_ok=True)
        for old_log in LOG_DIR.glob("*.log"):
            old_log.unlink(missing_ok=True)

    if config.option.log_file or is_xdist_controller:
        return
    config.option.log_file = str(LOG_DIR / (f"pytest_{worker_id}.log" if worker_id else "pytest.log"))


def pytest_addoption(parser):
    parser.addoption(
        "--browser_name",
        action="store",
        default="chrome",
        choices=SUPPORTED_BROWSERS,  # список браузеров берём из фабрики — один источник правды
        help="Browser to run tests in: chrome, firefox, or edge",
    )


# ==========================================
# 2. ПОЛЬЗОВАТЕЛИ И API
# ==========================================
@dataclass
class TempUser:
    """Временный пользователь и API-клиент, уже авторизованный под ним.

    Раньше фикстура возвращала словарь {"user": ..., "api": ...}.
    С dataclass опечатка в имени поля даёт понятную ошибку, а IDE подсказывает поля.
    """
    user: User
    api: PhonebookAPI


def _register_temp_user(step_title: str) -> TempUser:
    """Регистрирует нового уникального пользователя через API."""
    user = UserGenerator.get_valid_user()
    api = PhonebookAPI()

    with allure.step(f"Setup: {step_title} {user.email}"):
        response = api.register(user.email, user.password)
        require(
            response.status_code == 200,
            f"Не удалось зарегистрировать временного пользователя: {response.status_code} {response.text}",
        )
    return TempUser(user=user, api=api)


@pytest.fixture
def temp_user() -> TempUser:
    """Свой пользователь на каждый тест — полная изоляция данных (sandbox).

    Тесты не мешают друг другу даже при параллельном запуске через xdist.
    """
    return _register_temp_user("регистрация временного пользователя")


@pytest.fixture
def second_user() -> TempUser:
    """Второй независимый пользователь — для тестов доступа к чужим данным (BOLA)."""
    return _register_temp_user("регистрация второго временного пользователя")


@pytest.fixture
def auth_api(temp_user: TempUser) -> PhonebookAPI:
    """API-клиент, авторизованный под temp_user. Короткий путь для API-тестов."""
    return temp_user.api


# ==========================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# ==========================================
@pytest.fixture
def create_contact(auth_api: PhonebookAPI):
    """Фабрика: создаёт контакт через API и возвращает его вместе с id.

    Фикстура возвращает ФУНКЦИЮ, поэтому один тест может создать сколько угодно
    контактов, в том числе с нужными данными:

        def test_something(create_contact):
            first = create_contact()
            second = create_contact(name="Ivan")   # переопределение полей генератора
            first.id, first.phone                  # всё известно сразу
    """
    def _create(**overrides) -> Contact:
        contact = ContactGenerator.get_random_contact(**overrides)
        with allure.step(f"Setup: создание контакта через API (телефон {contact.phone})"):
            response = auth_api.add_contact(contact.to_api_payload())
            require(
                response.status_code == 200,
                f"Предусловие: контакт не создан: {response.status_code} {response.text}",
            )
            # replace() создаёт копию dataclass с изменённым полем
            return replace(contact, id=auth_api.find_contact_id(contact.phone))

    return _create


@pytest.fixture
def created_contact(create_contact) -> Contact:
    """Один готовый контакт с известным id — самый частый случай."""
    return create_contact()


# ==========================================
# 4. БРАУЗЕР SELENIUM
# ==========================================
@pytest.fixture
def driver(request):
    """Браузер для UI-теста. Как именно он создаётся — решает drivers/factory.py."""
    browser = request.config.getoption("--browser_name")
    raw_driver = create_driver(browser)
    session_id = raw_driver.session_id  # нужен, чтобы найти видео Selenoid после теста

    # Обёртка с listener'ом логирует действия (клики, переходы) — см. utils/listener.py
    decorated_driver = EventFiringWebDriver(raw_driver, PhonebookListener())

    yield decorated_driver

    if settings.use_selenoid:
        time.sleep(1.5)  # даём видеозаписи захватить последние кадры перед закрытием
    decorated_driver.quit()

    if settings.use_selenoid:
        attach_selenoid_video(session_id, browser)


@pytest.fixture
def authenticated_driver(driver, temp_user: TempUser):
    """Браузер, уже залогиненный через UI под temp_user."""
    with allure.step("Setup: UI-авторизация временного пользователя"):
        login_page = LoginPage(driver)
        login_page.open()
        login_page.login(temp_user.user.email, temp_user.user.password)
        require(login_page.is_signed_in(), "Setup: кнопка Sign Out не появилась после авторизации")
    return driver


# ==========================================
# 5. БРАУЗЕР PLAYWRIGHT
# ==========================================
@pytest.fixture
def page(context):
    """Переопределяем базовую фикстуру Playwright для авто-сохранения видео в Allure."""
    page = context.new_page()
    yield page

    video_path = page.video.path() if page.video else None

    page.close()
    context.close()

    if video_path and os.path.exists(video_path):
        allure.attach.file(
            video_path,
            name="Видео Playwright",
            attachment_type=allure.attachment_type.MP4,
        )


# ==========================================
# 6. ХУКИ ОТЧЁТНОСТИ
# ==========================================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """При падении UI-теста прикладывает к отчёту скриншот браузера."""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    driver = item.funcargs.get("driver") or item.funcargs.get("authenticated_driver")
    if not driver:
        return  # API-тест: браузера нет, скриншот не нужен

    # Открытый alert блокирует скриншот — закрываем его, если он есть
    try:
        driver.switch_to.alert.accept()
    except Exception:
        pass

    test_name = item.name.replace("/", "_").replace("::", "_")
    allure.attach(
        driver.get_screenshot_as_png(),
        name=f"Скриншот ошибки: {test_name}",
        attachment_type=allure.attachment_type.PNG,
    )


def pytest_make_parametrize_id(val):
    """
    Запрещает экранировать кириллицу и скрывает динамические адреса памяти (0x...)
    у lambda-функций, чтобы воркеры pytest-xdist собирали одинаковые ID тестов.
    """
    if callable(val):
        return "lambda_mutation"
    return str(val)


def pytest_sessionfinish(session):
    """Пишет блок Environment для Allure: где и как запускались тесты.

    Раньше он заполнялся только в GitHub Actions — вручную через echo.
    Теперь его пишет сам фреймворк, и информация есть в любом отчёте:
    локальном, Docker, Jenkins, CI.
    """
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return  # пишет только главный процесс, иначе воркеры перезапишут файл друг за другом

    results_dir = session.config.getoption("allure_report_dir", default=None)
    if not results_dir:
        return  # запуск без --alluredir: отчёта не будет, писать некуда

    if settings.use_selenoid:
        run_mode = "Selenoid"
    elif settings.headless or settings.is_ci:
        run_mode = "Local (headless)"
    else:
        run_mode = "Local"

    environment = {
        "Browser": session.config.getoption("--browser_name"),  # для Selenium; Playwright всегда chromium
        "RunMode": run_mode,
        "BaseUrl": settings.base_url,
        "ApiUrl": settings.api_url,
        "Python": platform.python_version(),
        "OS": f"{platform.system()} {platform.release()}",
    }
    Path(results_dir, "environment.properties").write_text(
        "\n".join(f"{key}={value}" for key, value in environment.items()) + "\n",
        encoding="utf-8",
    )
