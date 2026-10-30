"""Универсальные ожидания, не привязанные к Selenium."""

import time
from collections.abc import Callable


def eventually(condition: Callable[[], bool], timeout: float = 5.0, interval: float = 1.0) -> bool:
    """Опрашивает condition, пока оно не станет True или не выйдет время.

    Возвращает True, если условие выполнилось, и False по таймауту. Не бросает исключений,
    поэтому подходит для НЕГАТИВНЫХ проверок асинхронного поведения:

        # Правильно: даём приложению время "сделать плохое" и проверяем, что не сделало
        saved = eventually(lambda: contact_has_empty_email(), timeout=5)
        assert not saved, "Пустой email сохранился"

        # Неправильно: проверка сразу после клика.
        # Сохранение могло ещё не дойти до бэкенда, и тест "пройдёт" при живом баге.
    """
    deadline = time.monotonic() + timeout
    while True:
        if condition():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)
