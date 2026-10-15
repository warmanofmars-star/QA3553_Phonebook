import pytest
import allure
from data.data_generator import ContactGenerator
from utils.logger import get_logger

logger = get_logger("API_VALIDATION")
pytestmark = [pytest.mark.api, pytest.mark.regression]


@allure.epic("API Testing")
@allure.feature("Payload Validation")
@allure.story("Negative Contract Testing")
@pytest.mark.parametrize("scenario_key, expected_status, scenario", [
    ("missing_name", 400, "Без обязательного поля name"),
    ("empty_name", 400, "Пустая строка в name"),
    ("null_name", 400, "Null в обязательном поле name"),
    ("spaces_phone", 400, "Пробелы вместо телефона"),
    pytest.param(
        "boolean_name", 400, "Boolean вместо строки в name",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер кастует boolean в строку и возвращает 200")
    ),
    ("short_phone", 400, "Слишком короткий телефон (вне паттерна Swagger)"),
    ("invalid_email", 400, "Невалидный формат email"),
    pytest.param(
        "extra_fields", 400, "Отправка незадокументированных полей",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер молча игнорирует лишние поля вместо 400 Bad Request")
    )
])
def test_api_contact_payload_variations(auth_api, scenario_key, expected_status, scenario):
    logger.info(f"--- ЗАПУСК СЦЕНАРИЯ: {scenario} ---")

    contact = ContactGenerator.get_random_contact()
    payload = contact.to_api_payload()

    # Словарь мутаций прямо внутри теста
    mutations = {
        "missing_name": lambda p: p.pop("name"),
        "empty_name": lambda p: p.update({"name": ""}),
        "null_name": lambda p: p.update({"name": None}),
        "spaces_phone": lambda p: p.update({"phone": "   "}),
        "boolean_name": lambda p: p.update({"name": True}),
        "short_phone": lambda p: p.update({"phone": "123"}),
        "invalid_email": lambda p: p.update({"email": "not_an_email"}),
        "extra_fields": lambda p: p.update({"is_admin": True, "secret_hack": "123"})
    }

    # "Ломаем" пейлоад
    mutations[scenario_key](payload)

    with allure.step(f"Отправка сломанного payload: {scenario}"):
        response = auth_api.add_contact(payload)

    with allure.step("Проверка статуса и безопасности ответа"):
        assert response.status_code in [400, 422], \
            f"БАГ! Сервер ответил {response.status_code} на сценарий '{scenario}'"

        error_text = response.text.lower()
        forbidden_words = ["stack trace", "sql", "exception", "internal_id"]
        for word in forbidden_words:
            assert word not in error_text, f"УЯЗВИМОСТЬ: Утечка данных сервера! Найдено слово '{word}'"

    logger.info(f"[УСПЕХ] Сценарий '{scenario}' корректно заблокирован бэкендом.")