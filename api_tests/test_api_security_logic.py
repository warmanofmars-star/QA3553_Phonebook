import pytest
import allure
from api.contact_api import PhonebookAPI
from data.data_generator import UserGenerator, ContactGenerator
from utils.validators import assert_secure_error
from utils.logger import get_logger

logger = get_logger("API_SECURITY")
pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.regression]


@pytest.mark.xfail(reason="BUG BACKEND: При попытке удалить чужой контакт возвращается 400 вместо 403/404")
@allure.epic("API Security")
@allure.feature("BOLA (Broken Object Level Authorization)")
@allure.story("Accessing other user's data")
@allure.severity(allure.severity_level.BLOCKER)
def test_api_bola_delete_others_contact(temp_user):
    """Проверка 15: Пользователь А не должен иметь доступа к контакту Пользователя Б"""
    logger.info("--- ЗАПУСК ТЕСТА BOLA ---")

    api_user_a = temp_user["api"]  # Пользователь А (Алиса)

    # Регистрируем Пользователя Б (Боб)
    user_b_data = UserGenerator.get_valid_user()
    api_user_b = PhonebookAPI()
    api_user_b.register(user_b_data.email, user_b_data.password)

    # Боб создает контакт
    contact_b = ContactGenerator.get_random_contact()
    api_user_b.add_contact(contact_b.to_api_payload())

    # Получаем ID созданного контакта Боба через GET-запрос по контракту Swagger
    bob_contacts = api_user_b.get_contacts().json().get("contacts", [])
    contact_b_id = next(c.get("id") for c in bob_contacts if c.get("phone") == contact_b.phone)

    with allure.step("Атака: User A пытается удалить контакт User B"):
        attack_response = api_user_a.delete_contact(contact_b_id)

    with allure.step("Проверка отражения атаки"):
        assert attack_response.status_code != 200, "КРИТИЧЕСКАЯ УЯЗВИМОСТЬ BOLA! Алиса удалила контакт Боба!"
        assert attack_response.status_code in [403, 404, 401], \
            f"BOLA: Ожидался статус 403/404, получен {attack_response.status_code}"

        logger.info("[БЕЗОПАСНО] Бэкенд заблокировал доступ к чужому ресурсу.")


@allure.epic("API Logic")
@allure.feature("Idempotency")
@allure.story("Double DELETE operation")
@allure.severity(allure.severity_level.NORMAL)
def test_api_delete_idempotency(auth_api):
    """Проверка 19: Повторный запрос не должен ломать систему (Идемпотентность)"""
    logger.info("--- ЗАПУСК ТЕСТА ИДЕМПОТЕНТНОСТИ ---")

    contact = ContactGenerator.get_random_contact()
    auth_api.add_contact(contact.to_api_payload())

    contacts = auth_api.get_contacts().json().get("contacts", [])
    target_id = next(c.get("id") for c in contacts if c.get("phone") == contact.phone)

    res_first = auth_api.delete_contact(target_id)
    assert res_first.status_code == 200, "Первое удаление упало"

    with allure.step("Повторная отправка DELETE на уже удаленный ресурс"):
        res_second = auth_api.delete_contact(target_id)

    with allure.step("Проверка безопасной обработки дублирующего запроса"):
        assert res_second.status_code != 500, "БАГ! Сервер упал с 500 ошибкой при повторном удалении!"
        assert res_second.status_code in [400, 404], \
            f"Ожидалась ошибка отсутствия ресурса (400/404), получено: {res_second.status_code}"
        logger.info("[УСПЕХ] Система стабильна при дублирующих запросах.")


@allure.epic("API Security")
@allure.feature("HTTP Protocol")
@allure.story("HTTP Methods Restrictions (405)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG BACKEND: Spring Security возвращает 403/500 вместо 405 Method Not Allowed")
def test_api_security_method_not_allowed(auth_api):
    """Проверка: Сервер должен возвращать 405 при вызове неподдерживаемого HTTP-метода"""
    logger.info("--- ЗАПУСК ТЕСТА 405 METHOD NOT ALLOWED ---")
    url = f"{auth_api.BASE_URL}/v1/contacts/clear"

    with allure.step("Отправляем POST вместо DELETE на эндпоинт /v1/contacts/clear"):
        response = auth_api.session.post(url)

    assert_secure_error(response, 405)


@allure.epic("API Security")
@allure.feature("HTTP Protocol")
@allure.story("Content-Type Validation (415)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG BACKEND: Сервер возвращает 403/500 вместо 415 Unsupported Media Type")
def test_api_security_unsupported_media_type(auth_api):
    """Проверка: Сервер не должен пытаться парсить text/plain, если ожидает application/json"""
    logger.info("--- ЗАПУСК ТЕСТА 415 UNSUPPORTED MEDIA TYPE ---")
    url = f"{auth_api.BASE_URL}/v1/contacts"

    with allure.step("Отправляем обычный текст с заголовком text/plain вместо application/json"):
        headers = {"Content-Type": "text/plain"}
        response = auth_api.session.post(url, data="Malicious plain text payload", headers=headers)

    assert_secure_error(response, 415)