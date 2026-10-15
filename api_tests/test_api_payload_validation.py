import pytest
import allure
from data.data_generator import ContactGenerator
from utils.logger import get_logger

logger = get_logger("API_VALIDATION")
pytestmark = [pytest.mark.api, pytest.mark.regression]


@allure.epic("API Testing")
@allure.feature("Payload Validation")
@allure.story("Negative Contract Testing")
@pytest.mark.parametrize("modify_payload, expected_status, scenario", [
    # 6. Отсутствие обязательного поля
    (lambda p: p.pop("name"), 400, "Без обязательного поля name"),

    # 7. Пустые и null значения
    (lambda p: p.update({"name": ""}), 400, "Пустая строка в name"),
    (lambda p: p.update({"name": None}), 400, "Null в обязательном поле name"),
    (lambda p: p.update({"phone": "   "}), 400, "Пробелы вместо телефона"),

    # 8. Неправильный тип данных (строка вместо ожидаемого числа, если бы phone был int)
    # Предположим, мы передаем boolean вместо строки
    pytest.param(
        lambda p: p.update({"name": True}), 400, "Boolean вместо строки в name",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер кастует boolean в строку и возвращает 200")
    ),

    # 9. Граничные и недопустимые значения (Невалидный формат по RFC/Swagger)
    (lambda p: p.update({"phone": "123"}), 400, "Слишком короткий телефон (вне паттерна Swagger)"),
    (lambda p: p.update({"email": "not_an_email"}), 400, "Невалидный формат email"),

    # 10. Неизвестные/лишние поля (Проверка строгости контракта)
    pytest.param(
        lambda p: p.update({"is_admin": True, "secret_hack": "123"}), 400, "Отправка незадокументированных полей",
        marks=pytest.mark.xfail(reason="BUG BACKEND: Сервер молча игнорирует лишние поля вместо 400 Bad Request")
    )
])
def test_api_contact_payload_variations(auth_api, modify_payload, expected_status, scenario):
    """Единый параметризованный тест, покрывающий сразу 5 паттернов негативного тестирования API"""

    logger.info(f"--- ЗАПУСК СЦЕНАРИЯ: {scenario} ---")

    # Генерируем идеальный пейлоад
    contact = ContactGenerator.get_random_contact()
    payload = contact.to_api_payload()

    # "Ломаем" пейлоад с помощью lambda-функции из параметров
    modify_payload(payload)

    with allure.step(f"Отправка сломанного payload: {scenario}"):
        response = auth_api.add_contact(payload)

    with allure.step("Проверка статуса и безопасности ответа"):
        # Проверяем статус (Ожидаем 400 Bad Request или 422 Unprocessable Entity)
        # Если бэкенд возвращает 200 на эти запросы — это критический баг!
        assert response.status_code in [400, 422], \
            f"БАГ! Сервер ответил {response.status_code} на сценарий '{scenario}'"

        # Проверки 12-13: Безопасность тела ошибки
        error_text = response.text.lower()
        forbidden_words = ["stack trace", "sql", "exception", "internal_id"]
        for word in forbidden_words:
            assert word not in error_text, f"УЯЗВИМОСТЬ: Утечка данных сервера! Найдено слово '{word}'"

    logger.info(f"[УСПЕХ] Сценарий '{scenario}' корректно заблокирован бэкендом.")