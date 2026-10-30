"""
Фабрика WebDriver: создание браузера для всех режимов запуска.

Режимы (выбираются настройками из config.py):
  * Selenoid  (USE_SELENOID=true)  — браузер в Docker-контейнере, с VNC и видео.
  * Локально  (USE_SELENOID=false) — браузер на твоей машине;
                                     headless при HEADLESS_MODE=true или на CI.

Раньше всё это жило в фикстуре driver в conftest.py: 120 строк if/else,
где опции браузеров повторялись по 2–3 раза и успели разъехаться
(например, на CI у Edge и Firefox не задавался размер окна).
Теперь опции собираются в ОДНОМ месте — функции _build_options().
"""

import time
from pathlib import Path
from urllib.parse import urlsplit

import allure
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver

from config import settings
from utils.logger import get_logger

logger = get_logger("DRIVER")

SUPPORTED_BROWSERS = ("chrome", "firefox", "edge")

WINDOW_WIDTH, WINDOW_HEIGHT = 1920, 1080
PAGE_LOAD_TIMEOUT = 30  # секунды на полную загрузку страницы

# Как браузеры называются в Selenoid (ключи в selenoid/browsers.json)
SELENOID_BROWSER_NAMES = {"chrome": "chrome", "firefox": "firefox", "edge": "MicrosoftEdge"}

# Selenoid в Docker может стартовать чуть позже тестов (depends_on в compose
# ждёт только ЗАПУСКА контейнера, а не готовности сервиса). Поэтому перед
# созданием сессии ждём, пока Selenoid начнёт отвечать, но не дольше этого времени.
SELENOID_STARTUP_TIMEOUT = 30  # секунды
SELENOID_POLL_INTERVAL = 1     # пауза между проверками, секунды

# Сколько секунд ждать, пока Selenoid допишет видеофайл после закрытия сессии
VIDEO_WAIT_SECONDS = 10


# ==========================================
# Опции браузеров
# ==========================================
def _build_options(browser: str, headless: bool, ci: bool):
    """Собирает опции браузера. Единственное место, где они настраиваются."""
    if browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        # У Firefox свой синтаксис размера окна и языка
        options.add_argument(f"--width={WINDOW_WIDTH}")
        options.add_argument(f"--height={WINDOW_HEIGHT}")
        options.set_preference("intl.accept_languages", "en-US")
        return options

    # Edge построен на Chromium, поэтому аргументы у него те же, что у Chrome
    options = EdgeOptions() if browser == "edge" else ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
    options.add_argument("--lang=en-US")
    if ci:
        # Без этих флагов Chromium часто падает в контейнерах и на CI-раннерах:
        # нет песочницы ядра, маленький /dev/shm, нет GPU
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    return options


# ==========================================
# Создание драйвера
# ==========================================
def _create_remote_driver(browser: str) -> WebDriver:
    """Браузер в Selenoid. Видео и VNC включаются через selenoid:options."""
    if browser == "edge":
        # browsers.json сейчас описывает только chrome и firefox.
        # Лучше упасть сразу с понятной причиной, чем получить невнятную ошибку от Selenoid.
        raise ValueError("Edge не описан в selenoid/browsers.json — для Selenoid используй chrome или firefox")

    options = _build_options(browser, headless=False, ci=False)
    options.set_capability("browserName", SELENOID_BROWSER_NAMES[browser])
    options.set_capability("selenoid:options", {"enableVNC": True, "enableVideo": True})

    _wait_for_selenoid()
    logger.info(f"Создание сессии в Selenoid, браузер: {browser}")
    return webdriver.Remote(command_executor=settings.selenoid_hub_url, options=options)


def _wait_for_selenoid() -> None:
    """Ждёт, пока Selenoid начнёт отвечать на /status, либо падает с понятной ошибкой.

    Зачем отдельная проверка, а не повтор webdriver.Remote() в цикле:
    каждая неудачная попытка Remote() внутри ещё и сама ретраит соединение,
    и 5 попыток растягивались на ~90 секунд ради невнятного MaxRetryError.
    Лёгкий GET /status с коротким таймаутом отвечает на вопрос "жив ли Selenoid"
    за доли секунды.
    """
    # http://localhost:4444/wd/hub -> http://localhost:4444/status
    hub = urlsplit(settings.selenoid_hub_url)
    status_url = f"{hub.scheme}://{hub.netloc}/status"

    deadline = time.monotonic() + SELENOID_STARTUP_TIMEOUT
    logger.info(f"Проверка доступности Selenoid: {status_url}")
    while True:
        try:
            if requests.get(status_url, timeout=2).ok:
                return
        except requests.RequestException:
            pass  # соединение отклонено или таймаут — Selenoid ещё (или вообще) не запущен

        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Selenoid не отвечает на {status_url} уже {SELENOID_STARTUP_TIMEOUT} с.\n"
                "Варианты:\n"
                "  * запусти Selenoid:  docker compose up -d selenoid\n"
                "  * или запускай браузер локально: USE_SELENOID=false в .env "
                "(либо $env:USE_SELENOID=\"false\" в PowerShell на текущую сессию)"
            )
        time.sleep(SELENOID_POLL_INTERVAL)


def _create_local_driver(browser: str, headless: bool) -> WebDriver:
    """Браузер на локальной машине или CI-раннере."""
    options = _build_options(browser, headless=headless, ci=settings.is_ci)
    driver_classes = {"chrome": webdriver.Chrome, "firefox": webdriver.Firefox, "edge": webdriver.Edge}
    logger.info(f"Локальный запуск: {browser}, headless={headless}")
    return driver_classes[browser](options=options)


def create_driver(browser: str) -> WebDriver:
    """Создаёт и настраивает WebDriver для текущего режима запуска.

    Selenoid имеет приоритет: если USE_SELENOID=true, браузер всегда удалённый.
    """
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Неизвестный браузер {browser!r}, доступны: {', '.join(SUPPORTED_BROWSERS)}")

    if settings.use_selenoid:
        driver = _create_remote_driver(browser)
        headless = False  # в Selenoid браузер всегда "с окном" — его видно через VNC и на видео
    else:
        headless = settings.headless or settings.is_ci  # на CI-раннере экрана нет
        driver = _create_local_driver(browser, headless)

    # В headless размер окна уже задан опциями; maximize там ничего не даёт
    if not headless:
        driver.maximize_window()
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ==========================================
# Видео из Selenoid
# ==========================================
def attach_selenoid_video(session_id: str, browser: str) -> None:
    """Прикрепляет к Allure видео сессии, записанное Selenoid.

    Selenoid дописывает mp4 уже ПОСЛЕ закрытия сессии, поэтому файл
    может появиться не сразу — ждём его до VIDEO_WAIT_SECONDS секунд.
    """
    video_path = Path(settings.video_dir) / f"{session_id}.mp4"

    for _ in range(VIDEO_WAIT_SECONDS):
        if video_path.exists():
            time.sleep(1)  # файл появился, даём записи завершиться
            try:
                allure.attach(
                    video_path.read_bytes(),
                    name=f"Видео прохождения теста ({browser})",
                    attachment_type=allure.attachment_type.MP4,
                )
                logger.info(f"Видео {video_path.name} прикреплено к отчёту")
                return
            except OSError as error:
                # На Windows файл может быть ещё занят процессом записи — пробуем снова
                logger.warning(f"Видео пока недоступно для чтения: {error}")
        time.sleep(1)

    logger.warning(f"Видео {video_path.name} так и не появилось за {VIDEO_WAIT_SECONDS} с")
