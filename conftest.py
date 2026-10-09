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
from api.contact_api import PhonebookAPI
from pages.login_page import LoginPage
from data.data_generator import UserGenerator

# Загружаем переменные из .env
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
def driver(request):  # <--- Добавили request для чтения флага
    # Читаем наш флаг из консоли
    browser_name = request.config.getoption("--browser_name")

    # Читаем системные флаги
    is_headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    is_ci = os.environ.get('CI') == 'true'
    use_selenoid = os.getenv('USE_SELENOID', 'false').lower() == 'true'

    # Инициализируем переменные
    session_id = None
    driver_instance = None

    if is_ci:
        # ЗАПУСК В GITHUB ACTIONS
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
            # ЗАПУСК В DOCKER SELENOID
            print(f"\n[INFO] Маршрутизация в Docker Selenoid. Браузер: {browser_name}")

            # Подготавливаем опции и правильное имя для Селеноида
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

            # Читаем URL хаба
            hub_url = os.getenv("SELENOID_HUB_URL", "http://localhost:4444/wd/hub")

            # Умное ожидание готовности Селеноида (до 10 секунд)
            for attempt in range(5):
                try:
                    driver_instance = webdriver.Remote(
                        command_executor=hub_url,
                        options=options
                    )
                    break  # Подключились успешно
                except Exception as e:
                    if attempt == 4:
                        print(f"\n[ERROR] Селеноид так и не ответил: {e}")
                        raise e
                    print(f"\n[INFO] Ждем пробуждения Selenoid (попытка {attempt + 1})...")
                    time.sleep(2)

            session_id = driver_instance.session_id

        else:
            # ЛОКАЛЬНЫЙ ЗАПУСК НА КОМПЬЮТЕРЕ
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

    # Разворачиваем окно, если это не Headless
    if not is_headless and not use_selenoid:
        driver_instance.maximize_window()
    elif use_selenoid:
        driver_instance.maximize_window()

    driver_instance.set_page_load_timeout(30)

    # Подключаем листенер для красивых логов
    decorated_driver = EventFiringWebDriver(driver_instance, PhonebookListener())

    yield decorated_driver

    # Защита от сверхбыстрых тестов: даем FFmpeg время
    if use_selenoid:
        time.sleep(1.5)

    # Закрываем браузер
    decorated_driver.quit()

    # === ИНТЕГРАЦИЯ ВИДЕО В ALLURE ===
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
                            name=f"Видео прохождения теста ({browser_name})", # Указываем браузер в названии
                            attachment_type=allure.attachment_type.MP4
                        )
                    print(f"\n[INFO] Видео ({browser_name}) успешно прикреплено к отчету!")
                    break
                except Exception as e:
                    print(f"\n[WARNING] Файл заблокирован, пробуем снова. Ошибка: {e}")
            time.sleep(1)


@pytest.fixture
def authenticated_driver(driver, temp_user):
    login_page = LoginPage(driver)
    login_page.open()

    user = temp_user["user"]

    login_page.fill_email(user.email)
    login_page.fill_password(user.password)
    login_page.submit_login()

    login_page.is_logged()

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


@pytest.fixture(scope="function")
def auth_api(temp_user):
    """
    Фикстура-адаптер: берет изолированного API-клиента из песочницы (temp_user)
    и отдает его чистым API-тестам.
    """
    return temp_user["api"]


def pytest_make_parametrize_id(val):
    """
    Хук Pytest: запрещает экранировать кириллицу в ID параметризованных тестов.
    """
    return str(val)


@pytest.fixture
def temp_user():
    """
    Создает уникального пользователя через API для полной изоляции тестов.
    Возвращает объект User (email, password) и готовый API-клиент.
    """
    user = UserGenerator.get_valid_user()
    api = PhonebookAPI()

    with allure.step(f"Setup: Генерация временного пользователя {user.email}"):
        response = api.register(user.email, user.password)
        assert response.status_code == 200, "Не удалось зарегистрировать временного пользователя!"

    return {"user": user, "api": api}


@pytest.fixture
def page(context):
    """
    Переопределяем базовую фикстуру Playwright для авто-сохранения видео в Allure.
    Она прозрачно заменяет стандартный page во всех тестах.
    """
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