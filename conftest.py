import os
import time
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from dotenv import load_dotenv
from selenium.webdriver.support.events import EventFiringWebDriver
from utils.listener import PhonebookListener
from utils.logger import get_logger
from api.contact_api import PhonebookAPI
from pages.login_page import LoginPage
from data.data_generator import UserGenerator

load_dotenv()


def pytest_addoption(parser):
    parser.addoption(
        "--browser_name",
        action="store",
        default="chrome",
        choices=["chrome", "firefox", "edge"],
        help="Browser to run tests in: chrome, firefox, or edge"
    )


@pytest.fixture
def driver(request):
    browser_name = request.config.getoption("--browser_name")

    is_headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    is_ci = os.environ.get('CI') == 'true'
    use_selenoid = os.getenv('USE_SELENOID', 'false').lower() == 'true'

    session_id = None
    driver_instance = None

    if is_ci:
        if browser_name == "firefox":
            options = FirefoxOptions()
            options.add_argument('--headless')
            driver_instance = webdriver.Firefox(options=options)
        elif browser_name == "edge":
            options = EdgeOptions()
            options.add_argument('--headless')
            driver_instance = webdriver.Edge(options=options)
        else:
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
            print(f"\n[INFO] Маршрутизация в Docker Selenoid. Браузер: {browser_name}")

            if browser_name == "firefox":
                options = FirefoxOptions()
                selenoid_browser = "firefox"
            elif browser_name == "edge":
                options = EdgeOptions()
                selenoid_browser = "MicrosoftEdge"
            else:
                options = ChromeOptions()
                selenoid_browser = "chrome"

            options.set_capability("browserName", selenoid_browser)
            options.set_capability("selenoid:options", {
                "enableVNC": True,
                "enableVideo": True,
            })

            hub_url = os.getenv("SELENOID_HUB_URL", "http://localhost:4444/wd/hub")

            for attempt in range(5):
                try:
                    driver_instance = webdriver.Remote(
                        command_executor=hub_url,
                        options=options
                    )
                    break
                except Exception as e:
                    if attempt == 4:
                        print(f"\n[ERROR] Селеноид так и не ответил: {e}")
                        raise e
                    print(f"\n[INFO] Ждем пробуждения Selenoid (попытка {attempt + 1})...")
                    time.sleep(2)

            session_id = driver_instance.session_id
        else:
            try:
                if browser_name == "firefox":
                    options = FirefoxOptions()
                    if is_headless:
                        options.add_argument('--headless')
                    driver_instance = webdriver.Firefox(options=options)
                elif browser_name == "edge":
                    options = EdgeOptions()
                    if is_headless:
                        options.add_argument('--headless')
                    options.add_argument('--window-size=1920,1080')
                    options.add_argument('--lang=en-US')
                    driver_instance = webdriver.Edge(options=options)
                else:
                    options = ChromeOptions()
                    if is_headless:
                        options.add_argument('--headless=new')
                    options.add_argument('--window-size=1920,1080')
                    options.add_argument('--lang=en-US')
                    driver_instance = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"\n[WARNING] Не удалось запустить локальный {browser_name}. Причина: {e}")
                raise e

    if not is_headless and not use_selenoid:
        driver_instance.maximize_window()
    elif use_selenoid:
        driver_instance.maximize_window()

    driver_instance.set_page_load_timeout(30)
    decorated_driver = EventFiringWebDriver(driver_instance, PhonebookListener())

    yield decorated_driver

    if use_selenoid:
        time.sleep(1.5)

    decorated_driver.quit()

    if use_selenoid and session_id:
        video_dir = os.getenv("VIDEO_DIR", r"C:\selenoid\video")
        video_path = os.path.join(video_dir, f"{session_id}.mp4")

        for attempt in range(10):
            if os.path.exists(video_path):
                time.sleep(1)
                try:
                    with open(video_path, "rb") as video_file:
                        allure.attach(
                            video_file.read(),
                            name=f"Видео прохождения теста ({browser_name})",
                            attachment_type=allure.attachment_type.MP4
                        )
                    print(f"\n[INFO] Видео ({browser_name}) успешно прикреплено к отчету!")
                    break
                except Exception as e:
                    print(f"\n[WARNING] Файл заблокирован, пробуем снова. Ошибка: {e}")
            time.sleep(1)


@pytest.fixture
def authenticated_driver(driver, temp_user):
    """Автоматически логинится через UI под свежесозданным временным юзером (Sandbox)."""
    with allure.step("Setup Fixture: Автоматическая UI-авторизация (Sandbox)"):
        login_page = LoginPage(driver)
        login_page.open()

        user = temp_user["user"]
        login_page.login(user.email, user.password)

        assert login_page.is_logged(), "Setup Failed: Кнопка Sign Out не появилась после авторизации!"

    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        driver = item.funcargs.get('driver') or item.funcargs.get('authenticated_driver')

        if driver:
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except Exception:
                pass

            test_name = item.name.replace("/", "_").replace("::", "_")
            allure.attach(
                driver.get_screenshot_as_png(),
                name=f"Скриншот ошибки: {test_name}",
                attachment_type=allure.attachment_type.PNG
            )


@pytest.fixture
def temp_user():
    """Создает уникального пользователя через API для полной изоляции тестов."""
    user = UserGenerator.get_valid_user()
    api = PhonebookAPI()

    with allure.step(f"Setup Fixture: Генерация временного пользователя {user.email}"):
        response = api.register(user.email, user.password)
        assert response.status_code == 200, f"Не удалось зарегистрировать временного пользователя: {response.text}"

    return {"user": user, "api": api}


@pytest.fixture(scope="function")
def auth_api(temp_user):
    """Фикстура-адаптер: отдает изолированного API-клиента из песочницы (temp_user)."""
    return temp_user["api"]


def pytest_make_parametrize_id(val):
    """
    Запрещает экранировать кириллицу и скрывает динамические адреса памяти (0x...)
    у lambda-функций, чтобы воркеры pytest-xdist собирали одинаковые ID тестов.
    """
    if callable(val):
        return "lambda_mutation"
    return str(val)


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
            attachment_type=allure.attachment_type.MP4
        )


@pytest.fixture(scope="session")
def sys_logger():
    """Глобальная фикстура логгера для тестов."""
    return get_logger("TEST")