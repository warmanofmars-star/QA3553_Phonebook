"""
Реестр наблюдений: плохое поведение приложения, о котором в требованиях НИЧЕГО не сказано.

Чем наблюдение отличается от известного бага (data/known_bugs.py):
  * known_bug — нарушение конкретного требования (SRS, Swagger). Это дефект.
  * observation — требования нет (в SRS нефункциональные требования — "Nil"),
    но ожидание обосновано общепринятыми принципами: UX, семантикой HTTP и т.п.
    Это НЕ нарушение требования, а обоснованное ожидание. Решение — за аналитиком:
    подтвердить ожидание как требование или принять текущее поведение.

    @observation("DOUBLE_SUBMIT")
    def test_double_click_sends_one_post(...):

Механика та же, что у known_bug:
  * строгий xfail (strict=True): если поведение исправят, тест упадёт с XPASS —
    и наблюдение надо убрать из реестра, а тест оставить обычной проверкой;
  * raises=AssertionError: в xfail уходят только провалы проверок, а сбой окружения
    (таймаут, сеть, ошибка в коде теста) остаётся обычным FAILED;
  * причина xfail начинается с "[OBS-KEY]" — по ней наблюдение находит генератор
    матрицы покрытия (ci/coverage_matrix.py). Тег теста — OBS-<KEY>.

Правила для этого файла:
  1. Ключ — UPPER_SNAKE_CASE, описывает суть поведения.
  2. source — откуда ожидание (НЕ SRS: "общие принципы UX", "семантика HTTP 401"...).
  3. description — что приложение делает на самом деле.
  4. rationale — почему ожидание разумно, в одну-две фразы.
  5. Порядок — по важности: первым идёт то, что портит данные пользователя.
"""

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class Observation:
    source: str  # откуда ожидание (не требование)
    description: str  # фактическое поведение приложения
    rationale: str  # почему ожидание обосновано


OBSERVATIONS: dict[str, Observation] = {
    "DOUBLE_SUBMIT": Observation(
        source="Общие принципы UX: защита формы от повторной отправки",
        description="Кнопка Save не блокируется на время запроса: двойной клик отправляет два POST /v1/contacts",
        rationale="Пользователь создаёт два одинаковых контакта, не желая этого; бэкенд дубль не отклоняет",
    ),
    "SILENT_FAILURE": Observation(
        source="Общие принципы UX: видимость состояния системы, сообщение об ошибке",
        description="При 500 или обрыве сети на добавление, редактирование и удаление интерфейс ничего не сообщает",
        rationale="Пользователь не узнаёт, что действие не выполнено, и считает данные сохранёнными или удалёнными",
    ),
    "EDIT_FORM_CLOSES_ON_FAILURE": Observation(
        source="Общие принципы UX: не терять введённые пользователем данные",
        description="При сбое PUT /v1/contacts форма редактирования закрывается, введённые значения пропадают",
        rationale="Закрытие формы выглядит как успешное сохранение, а исправить и повторить уже нечего",
    ),
    "ENDLESS_LOADING": Observation(
        source="Общие принципы UX: у загрузки есть конец — данные, пустое состояние или ошибка",
        description="При 500 на GET /v1/contacts список навсегда остаётся в состоянии 'Loading...'",
        rationale="Пользователь ждёт бесконечно и не может отличить медленную сеть от сбоя",
    ),
    "EXPIRED_SESSION_NO_REDIRECT": Observation(
        source="Семантика HTTP 401 (RFC 9110): запрос требует аутентификации",
        description="При 401 на GET /v1/contacts интерфейс остаётся на /contacts с 'Loading...' и кнопкой Sign Out",
        rationale="Сессия недействительна, и единственное полезное действие — войти заново",
    ),
    "UNHANDLED_NETWORK_ERROR": Observation(
        source="Общие практики фронтенда: сетевые ошибки fetch перехватываются",
        description="При обрыве сети на POST /v1/contacts на странице необработанное исключение 'Failed to fetch'",
        rationale="Необработанное исключение — признак того, что ошибочный путь в коде не предусмотрен",
    ),
}


def observation(key: str) -> pytest.MarkDecorator:
    """Маркер xfail для наблюдения из реестра.

    Работает и как декоратор теста, и внутри pytest.param(..., marks=observation("...")).
    Тег OBS-<KEY> ставится на тест отдельно (@allure.tag) — его сверяет генератор матрицы.
    """
    if key not in OBSERVATIONS:
        raise KeyError(f"Неизвестное наблюдение {key!r}. Добавь его в data/observations.py с источником ожидания.")
    item = OBSERVATIONS[key]
    return pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason=f"[OBS-{key}] {item.description}. Не нарушение требования, а ожидание: {item.source}",
    )
