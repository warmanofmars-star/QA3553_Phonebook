"""Что страница сообщила пользователю и что сломалось в её коде — для Playwright-тестов.

    feedback = PwFeedback(page)      # подписаться ДО действия
    ...действие...
    feedback.error_shown(timeout_ms=5000)
    feedback.page_errors             # необработанные исключения страницы

Сообщение об ошибке — это alert/confirm (диалог) или видимый текст со словами ошибки.
Конкретного текста требования не задают, поэтому ищется любое явное сообщение.
"""

import re
import time

from playwright.sync_api import Dialog, Error, Page

# Слова, по которым видимый текст считается сообщением об ошибке
ERROR_TEXT = re.compile(r"error|fail|wrong|went wrong|try again|ошибк|не удалось", re.IGNORECASE)


class PwFeedback:
    def __init__(self, page: Page):
        self.page = page
        self.dialogs: list[str] = []
        self.page_errors: list[str] = []
        page.on("dialog", self._on_dialog)
        page.on("pageerror", self._on_page_error)

    def _on_dialog(self, dialog: Dialog) -> None:
        # Без обработчика Playwright закрыл бы диалог сам, но текст бы потерялся
        self.dialogs.append(f"{dialog.type}: {dialog.message}")
        dialog.accept()

    def _on_page_error(self, error: Error) -> None:
        self.page_errors.append(str(error))

    def error_texts(self) -> list[str]:
        """Видимые строки страницы, похожие на сообщение об ошибке."""
        lines = self.page.locator("body").inner_text().splitlines()
        return [line.strip() for line in lines if ERROR_TEXT.search(line)]

    def error_shown(self, timeout_ms: int) -> bool:
        """Появилось ли сообщение об ошибке (диалог или текст) за timeout_ms."""
        deadline = time.monotonic() + timeout_ms / 1000
        while True:
            if self.dialogs or self.error_texts():
                return True
            if time.monotonic() >= deadline:
                return False
            # wait_for_timeout, а не time.sleep: Playwright продолжает обрабатывать события
            self.page.wait_for_timeout(250)

    def describe(self) -> str:
        return f"диалоги: {self.dialogs or 'нет'}; текст ошибки: {self.error_texts() or 'нет'}"
