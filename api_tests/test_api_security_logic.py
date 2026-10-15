import pytest
import allure
from api.contact_api import PhonebookAPI
from data.data_generator import UserGenerator, ContactGenerator
from utils.logger import get_logger

logger = get_logger("API_SECURITY")
pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.regression]


@pytest.mark.xfail(reason="BUG BACKEND: При попытке удалить чужой контакт возвращается 400 вместо 403/404")
@allure.epic("API Security")
@allure.feature("BOLA (Broken Object Level Authorization)")
@allure.story("Accessing other user's data")
def test_api_bola_delete_others_contact(temp_user):
    """Проверка 15: Пользователь А не должен иметь доступа к контакту Пользователя Б"""
    logger.info("--- ЗАПУСК ТЕСТА BOLA ---")

    api_user_a = temp_user["api"]  # Это наш Алиса (User A)

    # Создаем Боба (User B) прямо в тесте
    user_b_data = UserGenerator.get_valid_user()
    api_user_b = PhonebookAPI()
    api_user_b.register(user_b_data.email, user_b_data.password)

    # Боб создает контакт
    contact_b = ContactGenerator.get_random_contact()
    res_create = api_user_b.add_contact(contact_b.to_api_payload())

    # Парсим ID созданного контакта Боба (предположим, API возвращает его в формате "id: 123"
    # или он отдается списком. Для примера сделаем GET всеми контактами Боба)
    bob_contacts = api_user_b.get_contacts().json().get("contacts", [])
    contact_b_id = next(c.get("id") for c in bob_contacts if c.get("phone") == contact_b.phone)

    # АЛИСА ПЫТАЕТСЯ УДАЛИТЬ КОНТАКТ БОБА
    with allure.step("Атака: User A пытается удалить контакт User B"):
        attack_response = api_user_a.delete_contact(contact_b_id)

    with allure.step("Проверка отражения атаки"):
        # Ожидаем 403 (Запрещено) или 404 (Не найдено, чтобы не "светить" чужие ID)
        assert attack_response.status_code in [403, 404, 401], \
            f"BOLA УЯЗВИМОСТЬ! Алиса смогла удалить контакт Боба! Статус: {attack_response.status_code}"

        logger.info("[БЕЗОПАСНО] Бэкенд заблокировал доступ к чужому ресурсу.")


@allure.epic("API Logic")
@allure.feature("Idempotency")
@allure.story("Double DELETE operation")
def test_api_delete_idempotency(auth_api):
    """Проверка 19: Повторный запрос не должен ломать систему (Идемпотентность)"""
    logger.info("--- ЗАПУСК ТЕСТА ИДЕМПОТЕНТНОСТИ ---")

    # Создаем контакт
    contact = ContactGenerator.get_random_contact()
    auth_api.add_contact(contact.to_api_payload())

    # Получаем его ID
    contacts = auth_api.get_contacts().json().get("contacts", [])
    target_id = next(c.get("id") for c in contacts if c.get("phone") == contact.phone)

    # Первый DELETE - должен быть успешен (200 OK)
    res_first = auth_api.delete_contact(target_id)
    assert res_first.status_code == 200, "Первое удаление упало"

    # Второй DELETE того же ID
    with allure.step("Повторная отправка DELETE на уже удаленный ресурс"):
        res_second = auth_api.delete_contact(target_id)

    with allure.step("Проверка безопасной обработки дублирующего запроса"):
        # Ожидаем 404 Not Found или 200/204 (если API спроектирован так, что DELETE всегда успешен)
        # Главное - не должно быть 500 Internal Server Error
        assert res_second.status_code != 500, "БАГ! Сервер упал с 500 ошибкой при повторном удалении!"
        assert res_second.status_code in [400,
                                          404], f"Ожидалась логичная ошибка (404), а пришло: {res_second.status_code}"
        logger.info("[УСПЕХ] Система стабильна при дублирующих запросах.")