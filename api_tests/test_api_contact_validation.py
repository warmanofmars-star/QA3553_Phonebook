"""Граничные значения и классы эквивалентности полей контакта (SRS T16–T44, T78–T82).

Ожидания — только из SRS. Каждый сценарий проверяет ровно одно правило:
остальные поля payload валидны (их генерирует ContactGenerator).

Как проверяется результат:
  * «принять»  — 200 и в списке появился ровно один новый контакт с теми же значениями;
  * «отклонить» — список контактов не изменился (главное: невалидные данные не сохранены)
    и сервер ответил 400. Состояние проверяется первым: если бэкенд сохранит
    мусор, тест скажет именно об этом, а не о «неправильном коде ответа».

Что уже покрыто в других файлах и здесь НЕ повторяется:
  test_api_payload_validation.py — пустое и null имя, телефон из пробелов, телефон "123",
  email без @, отсутствующие name/phone, пустой email.
"""

import random

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


# (поле API, значение, ожидание, требования SRS)
CONTACT_CASES = [
    # ---------- Телефон: длина (T41, T42) ----------
    pytest.param("phone", lambda: _phone(9), REJECT, ["T41"], id="phone-len-9"),
    pytest.param("phone", lambda: _phone(10), ACCEPT, ["T41"], id="phone-len-10"),
    pytest.param("phone", lambda: _phone(15), ACCEPT, ["T42"], id="phone-len-15"),
    pytest.param("phone", lambda: _phone(16), REJECT, ["T42"], id="phone-len-16"),
    # ---------- Телефон: только цифры (T40, T43, T44) ----------
    pytest.param("phone", "05012abcde", REJECT, ["T40", "T44"], id="phone-letters"),
    pytest.param("phone", "+972501234567", REJECT, ["T40", "T43"], id="phone-plus"),
    pytest.param("phone", "050-1234567", REJECT, ["T40", "T43"], id="phone-dash"),
    pytest.param("phone", "050 1234567", REJECT, ["T40"], id="phone-space"),
    # ---------- Имя (T17–T20) ----------
    pytest.param("name", "A", ACCEPT, ["T20"], id="name-1-char"),
    pytest.param("name", "   ", REJECT, ["T17"], id="name-spaces"),
    pytest.param("name", "12345", ACCEPT, ["T18"], id="name-digits"),
    pytest.param("name", "!@#$%^&*()_+-=", ACCEPT, ["T19"], id="name-special"),
    # ---------- Фамилия (T22–T25) ----------
    pytest.param("lastName", "B", ACCEPT, ["T25"], id="last-name-1-char"),
    # T22 в SRS говорит "Contact name" — опечатка: пункт в разделе фамилии, тег по смыслу
    pytest.param("lastName", "   ", REJECT, ["T22"], id="last-name-spaces"),
    pytest.param("lastName", "12345", ACCEPT, ["T23"], id="last-name-digits"),
    pytest.param("lastName", "!@#$%^&*()_+-=", ACCEPT, ["T24"], id="last-name-special"),
    # ---------- Адрес (T34–T37) ----------
    # T37 в SRS говорит "Contact name" — опечатка: пункт в разделе адреса, тег по смыслу
    pytest.param("address", "C", ACCEPT, ["T37"], id="address-1-char"),
    pytest.param("address", "   ", REJECT, ["T34"], id="address-spaces"),
    pytest.param("address", "12345", ACCEPT, ["T35"], id="address-digits"),
    pytest.param("address", "!@#$%^&*()_+-=", ACCEPT, ["T36"], id="address-special"),
    # ---------- Email (T28–T31) ----------
    pytest.param("email", "a@b", ACCEPT, ["T29", "T30"], id="email-min-a@b"),
    pytest.param("email", "user@mail@example.com", REJECT, ["T28"], id="email-two-at"),
    pytest.param("email", "@example.com", REJECT, ["T29"], id="email-nothing-before-at"),
    pytest.param("email", "user@", REJECT, ["T30"], id="email-nothing-after-at"),
    pytest.param("email", "пользователь@example.com", REJECT, ["T31"], id="email-cyrillic"),
    # ---------- null вместо обязательного значения (T21, T26, T33, T38) ----------
    # null в name уже проверяет test_api_payload_validation.py
    pytest.param("lastName", None, REJECT, ["T21"], id="last-name-null"),
    pytest.param("email", None, REJECT, ["T26"], id="email-null", marks=known_bug("EMAIL_NOT_REQUIRED")),
    pytest.param("address", None, REJECT, ["T33"], id="address-null"),
    pytest.param("phone", None, REJECT, ["T38"], id="phone-null", marks=known_bug("PHONE_NOT_REQUIRED")),
]


@allure.story("Create contact: boundary values and equivalence classes")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, value, expectation, requirements", CONTACT_CASES)
def test_api_contact_field_validation(auth_api, field, value, expectation, requirements):
    """POST /v1/contacts: одно поле с граничным или «особым» значением, остальные валидны."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    payload = ContactGenerator.get_random_contact().to_api_payload()
    # Случайные значения (телефоны) генерируются при запуске, а не при сборе тестов:
    # иначе воркеры pytest-xdist собрали бы разные данные
    payload[field] = value() if callable(value) else value

    if expectation == ACCEPT:
        _assert_accepted(auth_api, payload)
    else:
        _assert_rejected(auth_api, payload)


# Длина телефона при редактировании (T79, T80): те же границы, что при создании
UPDATE_PHONE_CASES = [
    pytest.param(9, REJECT, ["T79"], id="phone-len-9"),
    pytest.param(10, ACCEPT, ["T79"], id="phone-len-10"),
    pytest.param(15, ACCEPT, ["T80"], id="phone-len-15"),
    pytest.param(16, REJECT, ["T80"], id="phone-len-16"),
]


@allure.story("Update contact: phone length boundaries")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("length, expectation, requirements", UPDATE_PHONE_CASES)
def test_api_update_contact_phone_length(auth_api, created_contact, length, expectation, requirements):
    """PUT /v1/contacts: телефон граничной длины."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    original = created_contact.to_api_payload()
    payload = {**original, "phone": _phone(length)}

    response = auth_api.update_contact(payload)
    stored = next((c for c in auth_api.get_contacts_list() if c.get("id") == created_contact.id), {})
    stored_phone = stored.get("phone")

    if expectation == ACCEPT:
        assert response.status_code == 200, f"Валидный телефон отклонён: {response.status_code} {response.text}"
        assert stored_phone == payload["phone"], f"Телефон не обновился: сохранено {stored_phone!r}"
    else:
        assert stored_phone == original["phone"], (
            f"Сохранён телефон длины {length}: {stored_phone!r} (ответ {response.status_code})"
        )
        assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}: {response.text}"
