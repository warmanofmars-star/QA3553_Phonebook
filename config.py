"""
Единая точка конфигурации проекта.

ПРАВИЛО: переменные окружения читаются ТОЛЬКО в этом файле.
Все остальные модули берут настройки так:

    from config import settings
    url = f"{settings.api_url}/v1/contacts"

Откуда берутся значения (по убыванию приоритета):
  1. Реальные переменные окружения (Docker Compose, GitHub Actions, Jenkins).
  2. Файл .env в корне проекта (удобно для локального запуска).
  3. Значения по умолчанию, указанные ниже.

load_dotenv() НЕ перезаписывает уже существующие переменные окружения,
поэтому значение из CI всегда побеждает значение из локального .env.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта = папка, в которой лежит этот файл
PROJECT_ROOT = Path(__file__).resolve().parent

# Явно указываем путь к .env: так не важно, из какой папки запущен pytest
load_dotenv(PROJECT_ROOT / ".env")


# ==========================================
# Вспомогательные функции чтения переменных
# ==========================================
# Переменные окружения всегда строки. Эти функции приводят их к нужному типу
# и одинаково обрабатывают ситуацию "переменная не задана или пустая".

def _env_str(name: str, default: str | None = None) -> str | None:
    """Строка; пустое значение считается незаданным."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_bool(name: str, default: bool) -> bool:
    """Булево значение: true/1/yes/on (в любом регистре) считаются True."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("true", "1", "yes", "on")


def _env_int(name: str, default: int) -> int:
    """Целое число. При мусоре в переменной падаем СРАЗУ и с понятным сообщением,
    а не где-то в середине прогона с невнятной ошибкой."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Переменная окружения {name} должна быть целым числом, получено: {value!r}"
        ) from None


# ==========================================
# Настройки
# ==========================================
@dataclass(frozen=True)  # frozen=True: настройки нельзя случайно изменить во время прогона
class Settings:
    # --- Адреса тестируемого приложения ---
    base_url: str  # фронтенд (UI)
    api_url: str   # бэкенд (API)

    # --- Постоянный пользователь (нужен только части UI-тестов) ---
    user_email: str | None
    # repr=False: при print(settings) или логировании пароль не попадёт в вывод
    user_password: str | None = field(repr=False)

    # --- Запуск браузеров ---
    headless: bool          # запуск без окна браузера (локально)
    use_selenoid: bool      # True: браузеры в Docker через Selenoid
    selenoid_hub_url: str   # адрес Selenoid
    video_dir: str          # куда Selenoid складывает видео прогонов
    is_ci: bool             # True: запуск на "голом" CI-раннере без Selenoid

    # --- Таймауты ---
    ui_timeout: int         # явные ожидания Selenium, секунды
    pw_timeout_ms: int      # ожидания Playwright, миллисекунды

    @classmethod
    def from_env(cls) -> "Settings":
        """Собирает настройки из окружения. Вызывается один раз при импорте модуля."""
        return cls(
            # rstrip("/"): чтобы f"{api_url}/v1/..." никогда не давал двойной слэш
            base_url=_env_str("BASE_URL", "https://telranedu.web.app").rstrip("/"),
            api_url=_env_str("API_URL", "https://contactapp-telran-backend.herokuapp.com").rstrip("/"),

            user_email=_env_str("USER_EMAIL"),
            user_password=_env_str("USER_PASSWORD"),

            headless=_env_bool("HEADLESS_MODE", False),
            use_selenoid=_env_bool("USE_SELENOID", False),
            selenoid_hub_url=_env_str("SELENOID_HUB_URL", "http://localhost:4444/wd/hub"),
            video_dir=_env_str("VIDEO_DIR", r"C:\selenoid\video"),
            is_ci=_env_bool("CI", False),

            ui_timeout=_env_int("UI_TIMEOUT", 5),
            pw_timeout_ms=_env_int("PW_TIMEOUT", 10000),
        )


# Единственный экземпляр настроек на весь проект
settings = Settings.from_env()
