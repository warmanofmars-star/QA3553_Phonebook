"""
Реестр известных дефектов тестируемого приложения.

Приложение учебное и больше не поддерживается: найденные баги никто не исправит.
Поэтому тесты, которые на них натыкаются, помечаются как "ожидаемо падающие" (xfail).
Но помечаются НЕ как попало, а через этот реестр:

    @known_bug("DUPLICATE_CONTACT")
    def test_api_add_contact_duplicate(...):

Что это даёт:
  * Весь список дефектов проекта — в одном файле. Это и документация, и единый источник правды.
  * У каждого бага есть ссылка на требование: SRS (Google Docs) или Swagger (api-docs.json).
    Если ссылки нет — это не баг, а наше ожидание, и xfail ставить нельзя.
  * Опечатка в ключе даёт ошибку сразу при сборе тестов, а не тихий пропуск.
  * Все xfail строгие (strict=True): если тест вдруг ПРОЙДЁТ, прогон упадёт с XPASS.
    Это сигнал, что поведение изменилось и тест больше не проверяет то, что думаем.
  * raises=AssertionError: в xfail уходят ТОЛЬКО провалы проверок. Если тест упал
    по другой причине (таймаут Selenium, сеть, ошибка в коде теста), это обычный FAILED,
    и он не спрячется за "известным багом".

Правила для этого файла:
  1. Ключ — короткое имя в UPPER_SNAKE_CASE, описывает суть дефекта.
  2. requirement — откуда известно, что это баг (номер требования SRS или раздел Swagger).
  3. description — что приложение делает на самом деле.
"""

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class KnownBug:
    requirement: str   # на каком требовании основана проверка
    description: str   # фактическое (неправильное) поведение приложения


KNOWN_BUGS: dict[str, KnownBug] = {
    # ---------- Контакты: валидация и дубликаты ----------
    "DUPLICATE_CONTACT": KnownBug(
        requirement="SRS T32, T45, T83; Swagger: POST /v1/contacts -> 409 Duplicate contact fields",
        description="Бэкенд сохраняет контакт с уже существующими email/телефоном",
    ),
    "EMAIL_NOT_REQUIRED": KnownBug(
        requirement="SRS T26–T27, T64–T65 (Swagger поле email обязательным не считает)",
        description="Контакт с пустым email сохраняется (и при создании, и при редактировании)",
    ),
    "PHONE_NOT_REQUIRED": KnownBug(
        requirement="SRS T38–T39 (Swagger поле phone обязательным не считает)",
        description="Контакт без телефона сохраняется",
    ),
    "EDIT_DESCRIPTION_BROKEN": KnownBug(
        requirement="SRS раздел 2 (Update contact with valid data); STD TC-00026, TC-00027",
        description="При изменении описания через форму редактирования сохраняется строка '[object Undefined]'",
    ),
    "TYPE_COERCION": KnownBug(
        requirement="Swagger: ContactDto.name имеет type: string",
        description="Boolean в поле name молча приводится к строке, ответ 200",
    ),

    # ---------- API: контракт ответов ----------
    "NO_AUTH_403": KnownBug(
        requirement="Swagger: GET /v1/contacts -> 401 Unauthorized",
        description="Без заголовка Authorization сервер отвечает 403 с пустым телом",
    ),
    "NOT_FOUND_400": KnownBug(
        requirement="Swagger: DELETE /v1/contacts/{id} -> 404 Contact not found",
        description="Для несуществующего или чужого контакта сервер отвечает 400 вместо 404",
    ),
    "WRONG_CONTENT_TYPE_500": KnownBug(
        requirement="HTTP: ошибка клиента обрабатывается кодом 4xx, а не 5xx",
        description="На Content-Type text/plain сервер падает с 500 Internal Server Error",
    ),

    # ---------- API: права доступа ----------
    "CUSTOMER_CAN_CLEAR_ALL": KnownBug(
        requirement="SRS раздел 2, модуль 'Delete all contact': Customer — Can't",
        description="Обычный пользователь удаляет все свои контакты через DELETE /v1/contacts/clear (BFLA)",
    ),

    # ---------- UI: сообщения об ошибках ----------
    "NO_ERROR_ON_EMPTY_FIELD": KnownBug(
        requirement="SRS F5, F6, F9",
        description="При пустом обязательном поле форма не показывает сообщение об ошибке",
    ),
    "USER_EXISTS_WORDING": KnownBug(
        requirement="SRS F3: 'User already exists'",
        description="Приложение показывает 'User already exist' (без окончания -s)",
    ),
    "EMAIL_ERROR_WORDING": KnownBug(
        requirement="SRS F7: 'Email not valid: must have format email!'",
        description="Приложение показывает другой текст: 'must be a well-formed email address'",
    ),
}


def known_bug(key: str) -> pytest.MarkDecorator:
    """Маркер xfail для известного дефекта из реестра.

    Работает и как декоратор теста, и внутри pytest.param(..., marks=known_bug("...")).
    """
    if key not in KNOWN_BUGS:
        raise KeyError(f"Неизвестный баг {key!r}. Добавь его в data/known_bugs.py с ссылкой на требование.")
    bug = KNOWN_BUGS[key]
    return pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason=f"[{key}] {bug.description}. Требование: {bug.requirement}",
    )
