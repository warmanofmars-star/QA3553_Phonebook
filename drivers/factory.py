"""
Фабрика WebDriver: создание браузера для всех режимов запуска.

Режимы (выбираются настройками из config.py):
  * Selenium Grid (USE_GRID=true)  — браузер на узле Grid в Docker, с записью видео.
  * Локально      (USE_GRID=false) — браузер на твоей машине;
                                     headless при HEADLESS_MODE=true или на CI.

Раньше всё это жило в фикстуре driver в conftest.py: 120 строк if/else,
где опции браузеров повторялись по 2–3 раза и успели разъехаться
(например, на CI у Edge и Firefox не задавался размер окна).
Теперь опции собираются в ОДНОМ месте — функции _build_options().
"""

import time
from pathlib import Path

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

# Как браузеры называются в протоколе WebDriver (browserName). Их же Grid
# показывает в /status у слотов узлов — так мы проверяем, что нужный браузер есть
GRID_BROWSER_NAMES = {"chrome": "chrome", "firefox": "firefox", "edge": "MicrosoftEdge"}

# Узлы браузеров регистрируются в хабе через несколько секунд после старта контейнеров
# (depends_on в compose ждёт только ЗАПУСКА контейнера, а не готовности сервиса).
# Поэтому перед созданием сессии ждём, пока в Grid появится узел нужного браузера.
GRID_STARTUP_TIMEOUT = 60  # секунды: первый старт узлов бывает небыстрым
GRID_POLL_INTERVAL = 1  # пауза между проверками, секунды

# Сколько секунд ждать, пока узел допишет видеофайл после закрытия сессии
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
    """Браузер на узле Selenium Grid."""
    options = _build_options(browser, headless=False, ci=False)
    # Запись видео этой сессии (встроенный рекордер узла, см. docker-compose.yml).
    # Capability se:name НЕ задаём: тогда файл называется <id сессии>.mp4,
    # и после теста его легко найти (attach_session_video)
    options.set_capability("se:recordVideo", True)

    _wait_for_grid(browser)
    logger.info(f"Создание сессии в Selenium Grid, браузер: {browser}")
    return webdriver.Remote(command_executor=settings.grid_url, options=options)


def _grid_browsers(status: dict) -> set[str]:
    """Какие браузеры сейчас предлагают работающие узлы Grid (по слотам из /status)."""
    browsers = set()
    for node in status.get("value", {}).get("nodes", []):
        if node.get("availability", "UP") != "UP":
            continue  # узел уходит (DRAINING) или недоступен (DOWN)
        for slot in node.get("slots", []):
            name = slot.get("stereotype", {}).get("browserName")
            if name:
                browsers.add(name)
    return browsers


def _wait_for_grid(browser: str) -> None:
    """Ждёт, пока в Grid зарегистрируется узел нужного браузера, либо падает с понятной ошибкой.

    Проверяем не просто "хаб отвечает", а "есть узел именно этого браузера":
    хаб без узлов отвечает на /status, но сессию создать не сможет — запрос
    повиснет в очереди на 5 минут (таймаут Grid по умолчанию) и упадёт с невнятной ошибкой.
    """
    status_url = f"{settings.grid_url}/status"
    expected = GRID_BROWSER_NAMES[browser]
    available: set[str] = set()
    hub_answered = False

    deadline = time.monotonic() + GRID_STARTUP_TIMEOUT
    logger.info(f"Ожидание узла {browser} в Selenium Grid: {status_url}")
    while True:
        try:
            response = requests.get(status_url, timeout=2)
            hub_answered = True
            available = _grid_browsers(response.json())
            if expected in available:
                return
        except (requests.RequestException, ValueError):
            pass  # хаб ещё не поднялся (или ответ ещё не JSON) — пробуем снова

        if time.monotonic() >= deadline:
            if hub_answered:
                registered = ", ".join(sorted(available)) or "ни одного"
                raise RuntimeError(
                    f"В Selenium Grid нет узлов браузера {browser} (зарегистрировано: {registered}).\n"
                    f"Узлы запускаются по профилю: COMPOSE_PROFILES={browser} "
                    "(в .env или переменной окружения) — и тот же браузер в BROWSER."
                )
            raise RuntimeError(
                f"Selenium Grid не отвечает на {status_url} уже {GRID_STARTUP_TIMEOUT} с.\n"
                "Варианты:\n"
                f"  * запусти Grid:  COMPOSE_PROFILES={browser} docker compose up -d selenium-hub {browser}\n"
                "  * или запускай браузер локально: USE_GRID=false в .env "
                '(либо $env:USE_GRID="false" в PowerShell на текущую сессию)'
            )
        time.sleep(GRID_POLL_INTERVAL)


def _create_local_driver(browser: str, headless: bool) -> WebDriver:
    """Браузер на локальной машине или CI-раннере."""
    options = _build_options(browser, headless=headless, ci=settings.is_ci)
    driver_classes = {"chrome": webdriver.Chrome, "firefox": webdriver.Firefox, "edge": webdriver.Edge}
    logger.info(f"Локальный запуск: {browser}, headless={headless}")
    return driver_classes[browser](options=options)


def create_driver(browser: str) -> WebDriver:
    """Создаёт и настраивает WebDriver для текущего режима запуска.

    Grid имеет приоритет: если USE_GRID=true, браузер всегда удалённый.
    """
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Неизвестный браузер {browser!r}, доступны: {', '.join(SUPPORTED_BROWSERS)}")

    if settings.use_grid:
        driver = _create_remote_driver(browser)
        headless = False  # на узле Grid браузер всегда "с окном" — иначе на видео будет пустой экран
    else:
        headless = settings.headless or settings.is_ci  # на CI-раннере экрана нет
        driver = _create_local_driver(browser, headless)

    # В headless размер окна уже задан опциями; maximize там ничего не даёт
    if not headless:
        driver.maximize_window()
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


# ==========================================
# Видео сессии
# ==========================================
def attach_session_video(session_id: str, browser: str) -> None:
    """Прикрепляет к Allure видео сессии, записанное узлом Grid.

    Рекордер дописывает mp4 уже ПОСЛЕ закрытия сессии, поэтому файл
    может появиться не сразу — ждём его до VIDEO_WAIT_SECONDS секунд.
    """
    if not settings.video_dir:
        # Локальный запуск против Grid: видео лежит в Docker-томе, отсюда его не достать.
        # Раньше тест в этой ситуации 10 секунд ждал файл по несуществующему пути
        logger.debug("VIDEO_DIR не задан — видео к отчёту не прикладываем")
        return

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
