"""Сбои бэкенда для Playwright-тестов: ответ с нужным статусом, удержание запроса, обрыв сети.

    faults = NetworkFaults(page)
    puts = faults.respond(CONTACTS, "PUT", 500)       # PUT /v1/contacts получит 500
    held = faults.hold(CONTACTS, "GET")               # GET /v1/contacts повиснет...
    held.release()                                    # ...пока тест его не отпустит
    faults.abort(CONTACTS, "POST")                    # POST /v1/contacts — обрыв сети

Каждый метод возвращает список перехваченных запросов: по нему тест видит, сколько
запросов фактически ушло (например, после двойного клика).

Почему задержка — это "удержание", а не sleep: синхронный API Playwright выполняет
обработчики маршрутов в том же потоке, что и тест. time.sleep в обработчике заморозил бы
и сам тест — посмотреть на страницу во время задержки было бы нельзя. Удержанный запрос
висит, пока тест не вызовет release(): сначала тест проверяет индикатор загрузки, потом
отпускает запрос. Это и детерминированно — результат не зависит от скорости машины.

Запросы с другим методом уходят дальше (route.fallback): на один адрес можно
навесить несколько сбоев для разных методов.
"""

import time
from collections.abc import Callable

from playwright.sync_api import Page, Request, Route

from config import settings
from utils.preconditions import PreconditionError

# Адреса API (glob-шаблоны Playwright)
CONTACTS = "**/v1/contacts"  # список, создание, редактирование
CONTACT_BY_ID = "**/v1/contacts/*"  # удаление по id
LOGIN = "**/v1/user/login/**"

ERROR_BODIES = {
    401: {"status": 401, "error": "Unauthorized", "message": "Сбой, подставленный тестом"},
    403: {"status": 403, "error": "Forbidden", "message": "Сбой, подставленный тестом"},
    500: {"status": 500, "error": "Internal Server Error", "message": "Сбой, подставленный тестом"},
}


class HeldRequests:
    """Удержанные запросы: висят без ответа, пока тест не вызовет release()."""

    def __init__(self) -> None:
        self.routes: list[Route] = []
        self.requests: list[Request] = []
        self.released = False

    def __len__(self) -> int:
        return len(self.requests)

    def release(self) -> None:
        """Отпускает удержанные запросы на настоящий сервер (и все следующие — сразу).

        Важно: запросы фактически уходят, только пока тест вызывает Playwright. После
        release() ждать надо через Playwright (expect, page.wait_for_timeout), а не
        time.sleep — иначе за время ожидания запросы так и не дойдут до сервера.
        """
        self.released = True
        while self.routes:
            self.routes.pop(0).fallback()


class NetworkFaults:
    def __init__(self, page: Page):
        self.page = page

    def _intercept(self, url: str, method: str, action: Callable[[Route], None]) -> list[Request]:
        intercepted: list[Request] = []

        def handler(route: Route) -> None:
            if route.request.method != method:
                route.fallback()
                return
            intercepted.append(route.request)
            action(route)

        self.page.route(url, handler)
        return intercepted

    def respond(self, url: str, method: str, status: int, body: dict | None = None) -> list[Request]:
        """Ответ с заданным статусом и телом (по умолчанию — типичное тело ошибки)."""
        payload = body if body is not None else ERROR_BODIES.get(status, {})
        return self._intercept(url, method, lambda route: route.fulfill(status=status, json=payload))

    def abort(self, url: str, method: str) -> list[Request]:
        """Обрыв сети: браузер получает сетевую ошибку, ответа нет."""
        return self._intercept(url, method, lambda route: route.abort())

    def hold(self, url: str, method: str) -> HeldRequests:
        """Запрос висит без ответа до held.release(), затем уходит на настоящий сервер."""
        held = HeldRequests()

        def action(route: Route) -> None:
            if held.released:
                route.fallback()
            else:
                held.routes.append(route)

        held.requests = self._intercept(url, method, action)
        return held

    def wait_for_requests(self, requests, count: int = 1, timeout_ms: int | None = None) -> None:
        """Ждёт, пока перехвачено не меньше count запросов.

        Ожидание идёт через page.wait_for_timeout, а не time.sleep: пока тест ждёт,
        Playwright обрабатывает события страницы, в том числе перехват запросов.
        Не дождались — это предусловие (действие не дошло до сети), а не провал проверки:
        PreconditionError не спрячется за xfail известного бага или наблюдения.
        """
        timeout_ms = timeout_ms or settings.pw_timeout_ms
        deadline = time.monotonic() + timeout_ms / 1000
        while len(requests) < count:
            if time.monotonic() >= deadline:
                raise PreconditionError(f"За {timeout_ms} мс перехвачено {len(requests)} запросов из {count}")
            self.page.wait_for_timeout(100)
