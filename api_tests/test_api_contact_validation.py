"""Граничные значения и классы эквивалентности полей контакта.

Создание (POST) — SRS T16–T48, редактирование (PUT) — SRS T54–T86.

Раздел SRS "Update Contact" повторяет "New Contact" со сдвигом номеров на 38:
T(n) при создании = T(n+38) при редактировании (T16→T54 ... T48→T86). Поэтому
классы значений описаны ОДНОЙ таблицей FIELD_CASES, а оба теста (POST и PUT) берут
её же; номера требований для PUT получаются сдвигом (_update_requirements).

Ожидания — только из SRS. Каждый сценарий проверяет ровно одно правило:
остальные поля payload валидны (их генерирует ContactGenerator).

Как проверяется результат:
  * «принять»  — 200 и сохранённый контакт содержит отправленные значения
    (POST: в списке появился ровно один новый контакт; PUT: изменился контакт с тем же id);
  * «отклонить» — состояние не изменилось (POST: список контактов тот же; PUT: сохранённый
    контакт прежний) и сервер ответил 400. Состояние проверяется первым: если бэкенд
    сохранит мусор, тест скажет именно об этом, а не о «неправильном коде ответа».

Что POST уже проверяет в других файлах и здесь для него НЕ повторяется (в таблице такие
случаи помечены post=False и идут только в PUT-тест):
  test_api_payload_validation.py — пустое и null имя, телефон из пробелов, отсутствующие
  name/phone, пустой email, email без @.
"""

import random
from dataclasses import dataclass

import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug

pytestmark = [
    pytest.mark.api,
    pytest.mark.regression,
    allure.epic("API Testing"),
    allure.feature("Contact Field Validation"),
]

ACCEPT, REJECT = "accept", "reject"


def _phone(length: int) -> str:
    """Телефон из одних цифр заданной длины (уникальный в пределах временного пользователя)."""
    return "05" + "".join(random.choices("0123456789", k=length - 2))


def _new_contacts(api, before: list[dict]) -> list[dict]:
    """Контакты, которых не было в списке before."""
    known = {c.get("id") for c in before}
    return [c for c in api.get_contacts_list() if c.get("id") not in known]


def _assert_accepted(api, payload: dict) -> None:
    before = api.get_contacts_list()
    response = api.add_contact(payload)
    assert response.status_code == 200, f"Валидный контакт отклонён: {response.status_code} {response.text}"

    created = _new_contacts(api, before)
    assert len(created) == 1, f"Ожидался ровно один новый контакт, появилось {len(created)}"
    actual = {key: created[0].get(key) for key in payload}
    assert actual == payload, f"Сохранённые данные отличаются от отправленных:\n{actual}\n!=\n{payload}"


def _assert_rejected(api, payload: dict) -> None:
    before = api.get_contacts_list()
    response = api.add_contact(payload)

    created = _new_contacts(api, before)
    assert not created, f"Невалидный контакт сохранён (ответ {response.status_code}): {created}"
    assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}: {response.text}"


def _stored_contact(api, contact_id: str) -> dict:
    return next((c for c in api.get_contacts_list() if c.get("id") == contact_id), {})


# Поле отсутствует в payload (в отличие от None, который уходит как null)
ABSENT = object()

# Сдвиг номеров между разделами SRS: New Contact (T16–T48) -> Update Contact (T54–T86)
UPDATE_SHIFT = 38


def _update_requirements(requirements: list[str]) -> list[str]:
    """Номера требований раздела Update Contact по номерам раздела New Contact."""
    shifted = []
    for requirement in requirements:
        number = int(requirement.removeprefix("T"))
        if not 16 <= number <= 48:
            raise ValueError(f"{requirement} не из раздела New Contact (T16–T48): сдвиг неприменим")
        shifted.append(f"T{number + UPDATE_SHIFT}")
    return shifted


@dataclass(frozen=True)
class FieldCase:
    """Один класс значений поля контакта.

    requirements — номера раздела New Contact; для PUT они сдвигаются на 38.
    post=False — случай для POST уже проверен в другом файле (или не нужен), он только для PUT.
    post_bug / put_bug — ключ известного бага для POST и PUT по отдельности: поведение
    PUT на том же значении может отличаться от POST, поэтому ключи не общие.
    """

    id: str
    field: str
    value: object  # значение, функция без аргументов (случайные данные) или ABSENT
    expectation: str
    requirements: list[str]
    post: bool = True
    post_bug: str | None = None
    put_bug: str | None = None


FIELD_CASES = [
    # ---------- Телефон: длина (T41, T42) ----------
    FieldCase("phone-len-9", "phone", lambda: _phone(9), REJECT, ["T41"]),
    FieldCase("phone-len-10", "phone", lambda: _phone(10), ACCEPT, ["T41"]),
    FieldCase("phone-len-15", "phone", lambda: _phone(15), ACCEPT, ["T42"]),
    FieldCase("phone-len-16", "phone", lambda: _phone(16), REJECT, ["T42"]),
    # ---------- Телефон: только цифры (T40, T43, T44) ----------
    FieldCase("phone-letters", "phone", "05012abcde", REJECT, ["T40", "T44"]),
    FieldCase("phone-plus", "phone", "+972501234567", REJECT, ["T40", "T43"]),
    FieldCase("phone-dash", "phone", "050-1234567", REJECT, ["T40", "T43"]),
    FieldCase("phone-space", "phone", "050 1234567", REJECT, ["T40"]),
    # ---------- Имя (T17–T20) ----------
    FieldCase("name-1-char", "name", "A", ACCEPT, ["T20"]),
    FieldCase("name-spaces", "name", "   ", REJECT, ["T17"]),
    FieldCase("name-digits", "name", "12345", ACCEPT, ["T18"]),
    FieldCase("name-special", "name", "!@#$%^&*()_+-=", ACCEPT, ["T19"]),
    # ---------- Фамилия (T22–T25) ----------
    FieldCase("last-name-1-char", "lastName", "B", ACCEPT, ["T25"]),
    # T22 в SRS говорит "Contact name" — опечатка: пункт в разделе фамилии, тег по смыслу
    FieldCase("last-name-spaces", "lastName", "   ", REJECT, ["T22"]),
    FieldCase("last-name-digits", "lastName", "12345", ACCEPT, ["T23"]),
    FieldCase("last-name-special", "lastName", "!@#$%^&*()_+-=", ACCEPT, ["T24"]),
    # ---------- Адрес (T34–T37) ----------
    # T37 в SRS говорит "Contact name" — опечатка: пункт в разделе адреса, тег по смыслу
    FieldCase("address-1-char", "address", "C", ACCEPT, ["T37"]),
    FieldCase("address-spaces", "address", "   ", REJECT, ["T34"]),
    FieldCase("address-digits", "address", "12345", ACCEPT, ["T35"]),
    FieldCase("address-special", "address", "!@#$%^&*()_+-=", ACCEPT, ["T36"]),
    # ---------- Email (T28–T31) ----------
    FieldCase("email-min-a@b", "email", "a@b", ACCEPT, ["T29", "T30"]),
    FieldCase("email-two-at", "email", "user@mail@example.com", REJECT, ["T28"]),
    FieldCase("email-nothing-before-at", "email", "@example.com", REJECT, ["T29"]),
    FieldCase("email-nothing-after-at", "email", "user@", REJECT, ["T30"]),
    FieldCase(
        "email-cyrillic",
        "email",
        "пользователь@example.com",
        REJECT,
        ["T31"],
        post_bug="EMAIL_NON_LATIN_ALLOWED",
        put_bug="EMAIL_NON_LATIN_ALLOWED",
    ),
    # ---------- Описание (T47, T48) ----------
    FieldCase("description-digits", "description", "12345", ACCEPT, ["T47"]),
    FieldCase("description-special", "description", "!@#$%^&*()_+-=12345", ACCEPT, ["T48"]),
    # ---------- null вместо обязательного значения (T21, T26, T33, T38) ----------
    # null в name для POST проверяет test_api_payload_validation.py
    FieldCase("last-name-null", "lastName", None, REJECT, ["T21"]),
    FieldCase(
        "email-null", "email", None, REJECT, ["T26"], post_bug="EMAIL_NOT_REQUIRED", put_bug="EMAIL_NOT_REQUIRED"
    ),
    FieldCase("address-null", "address", None, REJECT, ["T33"]),
    FieldCase(
        "phone-null", "phone", None, REJECT, ["T38"], post_bug="PHONE_NOT_REQUIRED", put_bug="PHONE_NOT_REQUIRED"
    ),
    # ---------- Только для PUT ----------
    # Для POST эти классы проверены в test_api_payload_validation.py или в таблице не нужны
    FieldCase("name-null", "name", None, REJECT, ["T16"], post=False),
    FieldCase("name-absent", "name", ABSENT, REJECT, ["T16"], post=False),
    FieldCase("name-empty", "name", "", REJECT, ["T17"], post=False),
    FieldCase("last-name-absent", "lastName", ABSENT, REJECT, ["T21"], post=False),
    FieldCase("email-absent", "email", ABSENT, REJECT, ["T26"], post=False, put_bug="EMAIL_NOT_REQUIRED"),
    FieldCase("email-empty", "email", "", REJECT, ["T27"], post=False, put_bug="EMAIL_NOT_REQUIRED"),
    FieldCase("email-no-at", "email", "not_an_email", REJECT, ["T28"], post=False),
    FieldCase("address-absent", "address", ABSENT, REJECT, ["T33"], post=False),
    FieldCase("phone-absent", "phone", ABSENT, REJECT, ["T38"], post=False, put_bug="PHONE_NOT_REQUIRED"),
    FieldCase("phone-spaces", "phone", "   ", REJECT, ["T39"], post=False),
    FieldCase("description-absent", "description", ABSENT, ACCEPT, ["T46"], post=False),
]


def _params(*, update: bool) -> list:
    """Параметры pytest для POST или PUT: тот же набор классов, свои баги и номера SRS."""
    params = []
    for case in FIELD_CASES:
        if not update and not case.post:
            continue
        bug = case.put_bug if update else case.post_bug
        requirements = _update_requirements(case.requirements) if update else case.requirements
        params.append(
            pytest.param(
                case.field,
                case.value,
                case.expectation,
                requirements,
                id=case.id,
                marks=known_bug(bug) if bug else (),
            )
        )
    return params


def _build_payload(base: dict, field: str, value) -> dict:
    """Копия payload с одним изменённым полем.

    Случайные значения (телефоны) генерируются при запуске, а не при сборе тестов:
    иначе воркеры pytest-xdist собрали бы разные данные."""
    payload = dict(base)
    if value is ABSENT:
        payload.pop(field, None)
    else:
        payload[field] = value() if callable(value) else value
    return payload


@allure.story("Create contact: boundary values and equivalence classes")
@allure.tag("API-CHECK-9")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, value, expectation, requirements", _params(update=False))
def test_api_contact_field_validation(auth_api, field, value, expectation, requirements):
    """POST /v1/contacts: одно поле с граничным или «особым» значением, остальные валидны."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    payload = _build_payload(ContactGenerator.get_random_contact().to_api_payload(), field, value)

    if expectation == ACCEPT:
        _assert_accepted(auth_api, payload)
    else:
        _assert_rejected(auth_api, payload)


@allure.story("Update contact: boundary values and equivalence classes")
@allure.tag("API-CHECK-9")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, value, expectation, requirements", _params(update=True))
def test_api_update_contact_field_validation(auth_api, created_contact, field, value, expectation, requirements):
    """PUT /v1/contacts: те же классы значений, что для POST (номера SRS сдвинуты на 38).

    Меняется ровно одно поле существующего контакта, остальные остаются прежними."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    original = created_contact.to_api_payload()
    payload = _build_payload(original, field, value)

    response = auth_api.update_contact(payload)
    stored = _stored_contact(auth_api, created_contact.id)

    if expectation == ACCEPT:
        assert response.status_code == 200, f"Валидное значение отклонено: {response.status_code} {response.text}"
        actual = {key: stored.get(key) for key in payload}
        assert actual == payload, f"Сохранённые данные отличаются от отправленных:\n{actual}\n!=\n{payload}"
    else:
        # Состояние первым: контакт должен остаться прежним целиком, а не только изменяемое поле
        actual = {key: stored.get(key) for key in original}
        assert actual == original, (
            f"Контакт изменился при невалидном значении поля {field} (ответ {response.status_code}):\n"
            f"было {original}\nстало {actual}"
        )
        assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}: {response.text}"
