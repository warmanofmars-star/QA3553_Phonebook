import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from schemas.contact_schemas import ERROR_MESSAGE_SCHEMA
from utils.preconditions import require
from utils.validators import assert_json_schema, assert_secure_error

pytestmark = [pytest.mark.api, pytest.mark.regression]


@allure.epic("API Testing")
@allure.feature("Payload Validation")
@allure.story("Negative Contract Testing (DDT)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("API-CHECK-11", "API-CHECK-13")
@pytest.mark.parametrize(
    "mutate_func, expected_status, scenario",
    [
        # Теги — пункты SRS и номера проверок API, которые проверяет именно этот сценарий
        # Отсутствие обязательного поля
        pytest.param(
            lambda p: p.pop("name", None),
            400,
            "Без обязательного поля name",
            id="no-name",
            marks=allure.tag("SRS-T16", "API-CHECK-6"),
        ),
        pytest.param(
            lambda p: p.pop("phone", None),
            400,
            "Без телефона (SRS T38)",
            id="no-phone",
            marks=[known_bug("PHONE_NOT_REQUIRED"), allure.tag("SRS-T38", "API-CHECK-6")],
        ),
        # Пустые и null значения
        pytest.param(
            lambda p: p.update({"name": ""}),
            400,
            "Пустая строка в name",
            id="name-empty",
            marks=allure.tag("SRS-T17", "API-CHECK-7"),
        ),
        pytest.param(
            lambda p: p.update({"name": None}),
            400,
            "Null в обязательном поле name",
            id="name-null",
            marks=allure.tag("SRS-T16", "API-CHECK-7"),
        ),
        pytest.param(
            lambda p: p.update({"phone": "   "}),
            400,
            "Пробелы вместо телефона",
            id="phone-spaces",
            marks=allure.tag("SRS-T39", "API-CHECK-7"),
        ),
        pytest.param(
            lambda p: p.update({"email": ""}),
            400,
            "Пустой email (SRS T27)",
            id="email-empty",
            marks=[known_bug("EMAIL_NOT_REQUIRED"), allure.tag("SRS-T27", "API-CHECK-7")],
        ),
        # Неправильный тип данных
        pytest.param(
            lambda p: p.update({"name": True}),
            400,
            "Boolean вместо строки в name",
            id="name-boolean",
            marks=[known_bug("TYPE_COERCION"), allure.tag("API-CHECK-8")],
        ),
        # Граничные и недопустимые значения
        pytest.param(
            lambda p: p.update({"phone": "123"}),
            400,
            "Слишком короткий телефон (вне паттерна Swagger)",
            id="phone-short",
            marks=allure.tag("SRS-T41", "API-CHECK-8"),
        ),
        # Без SRS-тега: в адресе нет @ вовсе, а T28 говорит о «только одном @» —
        # прямой связи с конкретным пунктом нет
        pytest.param(
            lambda p: p.update({"email": "not_an_email"}),
            400,
            "Невалидный формат email",
            id="email-invalid",
            marks=allure.tag("API-CHECK-8"),
        ),
        # Сценарий "лишние поля -> 400" удалён: Swagger лишние поля не запрещает,
        # игнорировать неизвестные поля — нормальное поведение. Настоящая проверка
        # mass assignment — test_api_mass_assignment_foreign_id в test_api_security_logic.py
    ],
)
def test_api_contact_payload_variations(auth_api, mutate_func, expected_status, scenario):

    payload = ContactGenerator.get_random_contact().to_api_payload()
    mutate_func(payload)

    with allure.step(f"Отправка сломанного payload: {scenario}"):
        response = auth_api.add_contact(payload)

    assert_secure_error(response, expected_status)


@allure.epic("API Testing")
@allure.feature("Contract")
@allure.story("Error body matches ErrorMessageDto")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("API-CHECK-12")
def test_api_validation_error_body(auth_api):
    """Тело типичной ошибки валидации (400) соответствует ErrorMessageDto из Swagger,
    а status в теле совпадает с HTTP-статусом ответа."""
    payload = ContactGenerator.get_random_contact().to_api_payload()
    payload["name"] = ""

    response = auth_api.add_contact(payload)
    require(response.status_code == 400, f"Предусловие: ожидалась ошибка валидации, получено {response.status_code}")

    body = response.json()
    assert_json_schema(body, ERROR_MESSAGE_SCHEMA, "Тело ошибки")
    assert body["status"] == response.status_code, (
        f"status в теле ({body['status']}) не совпадает с HTTP-статусом ({response.status_code})"
    )
