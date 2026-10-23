import pytest
import allure
from data.data_generator import ContactGenerator
from utils.validators import assert_secure_error
from utils.logger import get_logger

logger = get_logger("API_VALIDATION")
pytestmark = [pytest.mark.api, pytest.mark.regression]


@allure.epic("API Testing")
@allure.feature("Payload Validation")
@allure.story("Negative Contract Testing (DDT)")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("mutate_func, expected_status, scenario", [
    # 6. Отсутствие обязательного поля
    (lambda p: p.pop("name", None), 400, "Без обязательного поля name"),

    # 7. Пустые и null значения
    (lambda p: p.update({"name": ""}), 400, "Пустая строка в name"),
    (lambda p: p.update({"name": None}), 400, "Null в обязательном поле name"),
    (lambda p: p.update({"phone": "   "}), 400, "Пробелы вместо телефона"),

    # 8. Неправильный тип данных
    pytest.param(
        lambda p: p.update({"name": True}), 400, "Boolean вместо строки в name",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер кастует boolean в строку и возвращает 200")
    ),

    # 9. Граничные и недопустимые значения
    (lambda p: p.update({"phone": "123"}), 400, "Слишком короткий телефон (вне паттерна Swagger)"),
    (lambda p: p.update({"email": "not_an_email"}), 400, "Невалидный формат email"),

    # 10. Неизвестные/лишние поля (Mass Assignment)
    pytest.param(
        lambda p: p.update({"is_admin": True, "secret_hack": "123"}), 400, "Отправка незадокументированных полей",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер молча игнорирует лишние поля вместо 400 Bad Request")
    )
])
def test_api_contact_payload_variations(auth_api, mutate_func, expected_status, scenario):
    logger.info(f"--- ЗАПУСК СЦЕНАРИЯ: {scenario} ---")

    contact = ContactGenerator.get_random_contact()
    payload = contact.to_api_payload()

    mutate_func(payload)

    with allure.step(f"Отправка сломанного payload: {scenario}"):
        response = auth_api.add_contact(payload)

    assert_secure_error(response, expected_status)
    logger.info(f"[УСПЕХ] Сценарий '{scenario}' корректно заблокирован бэкендом.")