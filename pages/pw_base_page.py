import time
from collections.abc import Callable

import allure
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PwTimeoutError

from config import settings
from pages.base_page import UiStateError
from utils.logger import get_logger

# Наблюдатель окна тишины: время последнего изменения DOM (performance.now()).
# Отсчёт начинается с установки — тишина до неё не засчитывается
_QUIET_OBSERVER_JS = """
() => {
  const state = { last: performance.now() };
  state.observer = new MutationObserver(() => { state.last = performance.now(); });
  state.observer.observe(document, { childList: true, attributes: true, characterData: true, subtree: true });
  window.__pwDomQuiet = state;
}
"""


class PwBasePage:
    def __init__(self, page: Page):
        self.page = page

        # Адрес и таймаут берём из единого конфига (тот же BASE_URL, что и у Selenium)
        self.base_url = settings.base_url
        self.expect_timeout = settings.pw_timeout_ms

        # Подключаем логгер с уникальным именем для Playwright
        self.logger = get_logger("PW")

    def open_url(self, path: str = ""):
        url = f"{self.base_url}{path}"
        self.logger.info(f"Переход по ссылке: {url}")

        with allure.step(f"Открытие URL: {url}"):
            self.page.goto(url)

    def fill(self, locator: Locator, value: str, is_secret: bool = False):
        """Универсальный метод ввода с логированием и маскировкой Allure"""
        display_value = "********" if is_secret else value

        self.logger.info("Ввод данных в поле формы...")
        with allure.step(f"Ввод текста '{display_value}'"):
            locator.fill(value)

    def wait_until(self, condition: Callable[[], bool], timeout_ms: int) -> bool:
        """Ждёт, пока condition() станет True; False — по таймауту (исключений не бросает).

        Пауза — page.wait_for_timeout, а не time.sleep: синхронный Playwright обрабатывает
        события страницы (ответы, диалоги, перехват сети) только во время своих вызовов.
        """
        deadline = time.monotonic() + timeout_ms / 1000
        while not condition():
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(250)
        return True

    def wait_dom_quiet(self, quiet_ms: int, timeout_ms: int | None = None) -> None:
        """Ждёт, пока DOM не меняется quiet_ms подряд (каждое изменение сбрасывает отсчёт).

        Для негативных проверок ("значение НЕ изменилось"): у события "ничего не произошло"
        нет сигнала, поэтому после доставки ответа ждём, пока приложение перестанет менять
        страницу. Граница: реакцию, пришедшую позже окна (например, по таймеру), проверка
        не увидит — как не видела и фиксированная пауза.

        Не успокоилась за timeout_ms — UiStateError, а не AssertionError: несинхронизированная
        страница не должна прятаться за строгим xfail наблюдения или известного бага.
        """
        timeout_ms = timeout_ms or self.expect_timeout
        self.page.evaluate(_QUIET_OBSERVER_JS)
        try:
            self.page.wait_for_function(
                "quiet => performance.now() - window.__pwDomQuiet.last >= quiet", arg=quiet_ms, timeout=timeout_ms
            )
        except PwTimeoutError as error:
            raise UiStateError(f"DOM не утих на {quiet_ms} мс за {timeout_ms} мс") from error
        finally:
            # Страница могла уйти (навигация) — тогда отключать уже нечего
            self.page.evaluate("() => window.__pwDomQuiet && window.__pwDomQuiet.observer.disconnect()")

    def click(self, locator: Locator, element_name: str = "Элемент"):
        """Универсальный клик с логированием"""
        self.logger.info(f"Клик по элементу: '{element_name}'")

        with allure.step(f"Клик по элементу: {element_name}"):
            locator.click()
