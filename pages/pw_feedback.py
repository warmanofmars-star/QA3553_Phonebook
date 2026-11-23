"""Что страница сообщила пользователю и что сломалось в её коде — для Playwright-тестов.

    feedback = PwFeedback(page)      # подписаться ДО действия
    ...подготовка...
    feedback.before_action(*введённые_тестом_значения)   # непосредственно перед действием
    ...действие...
    feedback.error_shown(timeout_ms=5000)
    feedback.page_errors             # необработанные исключения страницы

Сообщение об ошибке — это alert/confirm (диалог) или видимый текст со словами ошибки,
появившийся после действия. Конкретного текста требования не задают, поэтому ищется
любое явное сообщение.

Без before_action() детектор падает с PreconditionError (error_texts, error_shown):
по всему тексту страницы он принимал бы данные теста за сообщение приложения.
Диалоги и page_errors собираются и читаются без before_action().
"""

import re
import time
from collections import Counter

from playwright.sync_api import Dialog, Error, Page

from utils.preconditions import PreconditionError

# Слова, по которым видимый текст считается сообщением об ошибке
ERROR_TEXT = re.compile(r"error|fail|wrong|went wrong|try again|ошибк|не удалось", re.IGNORECASE)


class PwFeedback:
    def __init__(self, page: Page):
        self.page = page
        self.dialogs: list[str] = []
        self.page_errors: list[str] = []
        self._baseline: Counter[str] = Counter()
        self._entered: list[str] = []
        self._prepared = False
        page.on("dialog", self._on_dialog)
        page.on("pageerror", self._on_page_error)

    def _on_dialog(self, dialog: Dialog) -> None:
        # Без обработчика Playwright закрыл бы диалог сам, но текст бы потерялся
        self.dialogs.append(f"{dialog.type}: {dialog.message}")
        dialog.accept()

    def _on_page_error(self, error: Error) -> None:
        self.page_errors.append(str(error))

    def before_action(self, *entered: str) -> None:
        """Вызвать непосредственно перед сбойным действием.

        Данные теста — случайный текст Faker, а в его словаре en_US есть слово «wrong»:
        примерно 0,6 % предложений fake.sentence() его содержат. Описание контакта видно
        в открытой карточке, и детектор принимал его за сообщение приложения — ложный XPASS.
        Поэтому:
          * строки, похожие на ошибку и видимые ещё ДО действия, не считаются (с учётом
            повторов: такая же новая строка сверх запомненных — считается);
          * из строки перед проверкой вырезаются только значения, введённые самим тестом.
            Остальной текст не трогаем: «Error saving John» — сообщение приложения.
        Диалоги считаются всегда: диалог открывает само приложение, данных теста в нём нет.

        Вызов обязателен: без него error_texts() и error_shown() падают с PreconditionError.
        Защита закрыта по умолчанию — тест, забывший вызов, краснеет, а не получает ложный XPASS.
        """
        # Длинные значения первыми: короткое (имя) не должно разрезать длинное (новое имя)
        self._entered = sorted({value for value in entered if value}, key=len, reverse=True)
        self._baseline = Counter(self._error_lines())
        self._prepared = True

    def _require_prepared(self) -> None:
        # PreconditionError, а не assert: строгий xfail наблюдения ловит только AssertionError,
        # и забытый вызов спрятался бы за ожидаемым падением
        if not self._prepared:
            raise PreconditionError(
                "PwFeedback: перед сбойным действием вызовите feedback.before_action(<значения, "
                "введённые тестом>). Без него детектор ищет слова ошибки по всему тексту страницы "
                "и принимает данные теста (например, описание Faker со словом «wrong») "
                "за сообщение приложения"
            )

    def _error_lines(self) -> list[str]:
        """Все видимые строки страницы, похожие на ошибку, если убрать из них данные теста."""
        found = []
        for raw in self.page.locator("body").inner_text().splitlines():
            line = raw.strip()
            own_text = line
            for value in self._entered:
                own_text = own_text.replace(value, "")
            if ERROR_TEXT.search(own_text):
                found.append(line)
        return found

    def error_texts(self) -> list[str]:
        """Строки, похожие на сообщение об ошибке и появившиеся после before_action."""
        self._require_prepared()
        already_seen = self._baseline.copy()
        new_lines = []
        for line in self._error_lines():
            if already_seen[line] > 0:
                already_seen[line] -= 1
            else:
                new_lines.append(line)
        return new_lines

    def error_shown(self, timeout_ms: int) -> bool:
        """Появилось ли сообщение об ошибке (диалог или текст) за timeout_ms."""
        # Проверка до цикла: иначе при уже пойманном диалоге забытый вызов прошёл бы незамеченным
        self._require_prepared()
        deadline = time.monotonic() + timeout_ms / 1000
        while True:
            if self.dialogs or self.error_texts():
                return True
            if time.monotonic() >= deadline:
                return False
            # wait_for_timeout, а не time.sleep: Playwright продолжает обрабатывать события
            self.page.wait_for_timeout(250)

    def describe(self) -> str:
        # Диагностика для сообщений и отчётов не должна сама падать: без before_action
        # текст не проверяется, а прямо говорится, что сравнивать не с чем
        texts = (self.error_texts() or "нет") if self._prepared else "не проверялся: before_action() не вызывался"
        return f"диалоги: {self.dialogs or 'нет'}; текст ошибки: {texts}"
