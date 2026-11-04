"""Валидация регистрации: пароль (SRS T9–T15) и email (SRS T3–T6).

Валидный пароль собирается из «признаков» (заглавная, строчная, цифра, спецсимвол, длина),
и каждый негативный сценарий меняет РОВНО ОДИН признак. Тогда отказ сервера
однозначно указывает на проверяемое правило, а не на случайное совпадение нескольких.

Как проверяется результат:
  * «принять»  — 200, и с этими данными можно войти (пользователь действительно создан);
  * «отклонить» — войти с этими данными нельзя (пользователь не создан) и сервер ответил 400.
"""

import uuid

import allure
import pytest

from api.contact_api import PhonebookAPI
from data.data_generator import UserGenerator
from data.known_bugs import known_bug

pytestmark = [
    pytest.mark.api,
    pytest.mark.regression,
    allure.epic("API Testing"),
    allure.feature("Registration Validation"),
]

ACCEPT, REJECT = "accept", "reject"
ALLOWED_SPECIAL = "@$#^&*!"  # SRS T9


def _password(length: int = 10, *, upper: bool = True, lower: bool = True, digit: bool = True, special: str = "!"):
    """Пароль заданной длины с нужным набором признаков.

    Обязательные символы идут первыми, остаток добирается одной буквой-заполнителем:
    строчной, а если строчные запрещены сценарием — заглавной.
    """
    required = ("A" if upper else "") + ("b" if lower else "") + ("1" if digit else "") + special
    filler = "c" if lower else "C"
    return required + filler * (length - len(required))


def _unique() -> str:
    return uuid.uuid4().hex[:10]


def _assert_registration(email: str, password: str, expectation: str) -> None:
    response = PhonebookAPI().register(email, password)
    # Состояние: создан ли пользователь — проверяем входом новым клиентом
    login = PhonebookAPI().login(email, password)

    if expectation == ACCEPT:
        assert response.status_code == 200, f"Валидные данные отклонены: {response.status_code} {response.text}"
        assert login.status_code == 200, f"Регистрация ответила 200, но войти нельзя: {login.status_code}"
    else:
        assert login.status_code != 200, f"Создан пользователь с невалидными данными (ответ {response.status_code})"
        assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}: {response.text}"


PASSWORD_CASES = [
    # ---------- Длина (T14, T15) ----------
    pytest.param(lambda: _password(7), REJECT, ["T14"], id="len-7"),
    pytest.param(lambda: _password(8), ACCEPT, ["T14"], id="len-8"),
    pytest.param(lambda: _password(15), ACCEPT, ["T15"], id="len-15"),
    pytest.param(lambda: _password(16), REJECT, ["T15"], id="len-16", marks=known_bug("PASSWORD_NO_MAX_LENGTH")),
    # ---------- Обязательные классы символов (T9, T11–T13) ----------
    pytest.param(lambda: _password(upper=False), REJECT, ["T11"], id="no-uppercase"),
    pytest.param(lambda: _password(lower=False), REJECT, ["T12"], id="no-lowercase"),
    pytest.param(lambda: _password(digit=False), REJECT, ["T13"], id="no-digit"),
    pytest.param(lambda: _password(special=""), REJECT, ["T9"], id="no-special"),
    # % не входит в список T9: спецсимвол есть, но не из разрешённых
    pytest.param(lambda: _password(special="%"), REJECT, ["T9"], id="special-not-from-list"),
    # ---------- Только английские буквы (T10) ----------
    # Все признаки валидного пароля на месте, одна буква-заполнитель заменена кириллической
    pytest.param(
        lambda: _password()[:-1] + "ж",
        REJECT,
        ["T10"],
        id="cyrillic-letter",
        marks=known_bug("PASSWORD_NON_LATIN_ALLOWED"),
    ),
]


@allure.story("Password rules")
@allure.tag("API-CHECK-9")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("make_password, expectation, requirements", PASSWORD_CASES)
def test_api_registration_password(make_password, expectation, requirements):
    """POST /v1/user/registration/usernamepassword: пароль меняет ровно один признак, email валиден."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    _assert_registration(UserGenerator.generate_valid_email(), make_password(), expectation)


# Email должен быть уникальным: повторная регистрация того же адреса отклонялась бы
# по другой причине. Поэтому минимум "1 символ до @" и "1 символ после @" проверяются
# раздельно: вторая часть адреса делает его уникальным
EMAIL_CASES = [
    pytest.param(lambda: f"a@{_unique()}.com", ACCEPT, ["T4"], id="one-char-before-at"),
    pytest.param(lambda: f"{_unique()}@b", ACCEPT, ["T5"], id="one-char-after-at"),
    pytest.param(lambda: f"{_unique()}@mail@example.com", REJECT, ["T3"], id="two-at"),
    pytest.param(lambda: f"@{_unique()}.com", REJECT, ["T4"], id="nothing-before-at"),
    pytest.param(lambda: f"{_unique()}@", REJECT, ["T5"], id="nothing-after-at"),
    pytest.param(
        lambda: f"пользователь{_unique()}@example.com",
        REJECT,
        ["T6"],
        id="cyrillic",
        marks=known_bug("EMAIL_NON_LATIN_ALLOWED"),
    ),
]


@allure.story("Email rules")
@allure.tag("API-CHECK-9")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("make_email, expectation, requirements", EMAIL_CASES)
def test_api_registration_email(make_email, expectation, requirements):
    """POST /v1/user/registration/usernamepassword: email на границе правил T3–T6, пароль валиден."""
    allure.dynamic.tag(*(f"SRS-{r}" for r in requirements))
    _assert_registration(make_email(), UserGenerator.generate_valid_password(), expectation)
