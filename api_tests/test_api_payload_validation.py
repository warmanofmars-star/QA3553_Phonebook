import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from utils.logger import get_logger
from utils.validators import assert_secure_error

logger = get_logger("API_VALIDATION")
pytestmark = [pytest.mark.api, pytest.mark.regression]


@allure.epic("API Testing")
@allure.feature("Payload Validation")
@allure.story("Negative Contract Testing (DDT)")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("mutate_func, expected_status, scenario", [
    # Отсутствие обязательного поля
    (lambda p: p.pop("name", None), 400, "Без обязательного поля name"),
    pytest.param(
        lambda p: p.pop("phone", None), 400, "Без телефона (SRS T38)",
        marks=known_bug("PHONE_NOT_REQUIRED"),
    ),

    # Пустые и null значения
    (lambda p: p.update({"name": ""}), 400, "Пустая строка в name"),
    (lambda p: p.update({"name": None}), 400, "Null в обязательном поле name"),
    (lambda p: p.update({"phone": "   "}), 400, "Пробелы вместо телефона"),
    pytest.param(
        lambda p: p.update({"email": ""}), 400, "Пустой email (SRS T27)",
        marks=known_bug("EMAIL_NOT_REQUIRED"),
    ),

    # Неправильный тип данных
    pytest.param(
        lambda p: p.update({"name": True}), 400, "Boolean вместо строки в name",
        marks=known_bug("TYPE_COERCION"),
    ),

    # Граничные и недопустимые значения
    (lambda p: p.update({"phone": "123"}), 400, "Слишком короткий телефон (вне паттерна Swagger)"),
    (lambda p: p.update({"email": "not_an_email"}), 400, "Невалидный формат email"),

    # Сценарий "лишние поля -> 400" удалён: Swagger лишние поля не запрещает,
    # игнорировать неизвестные поля — нормальное поведение. Настоящая проверка
    # mass assignment — test_api_mass_assignment_foreign_id в test_api_security_logic.py
])
def test_api_contact_payload_variations(auth_api, mutate_func, expected_status, scenario):
    logger.info(f"--- ЗАПУСК СЦЕНАРИЯ: {scenario} ---")

    payload = ContactGenerator.get_random_contact().to_api_payload()
    mutate_func(payload)

    with allure.step(f"Отправка сломанного payload: {scenario}"):
        response = auth_api.add_contact(payload)

    assert_secure_error(response, expected_status)
    logger.info(f"[УСПЕХ] Сценарий '{scenario}' корректно заблокирован бэкендом.")
