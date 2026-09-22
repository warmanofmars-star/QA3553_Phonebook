import allure
import pytest
import os
from utils.api_helper import make_api_request
from data.data_generator import ContactGenerator
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
API_URL = os.getenv("API_URL")
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'
logger = get_logger("API")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Delete Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_delete_contact(api_token):
    """Тест удаления конкретного контакта (Delete)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем контакт и узнаем его ID
    contact = ContactGenerator.get_random_contact()
    make_api_request("POST", f"{API_URL}/v1/contacts", json=contact.to_api_payload(), headers=headers)

    response_get = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list = response_get.json().get("contacts", [])

    target_id = None
    for c in contacts_list:
        if c.get("phone") == contact.phone:
            target_id = c.get("id")
            break

    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    # 2. ШАГ ТЕСТА: Удаляем контакт по ID
    response_delete = make_api_request("DELETE", f"{API_URL}/v1/contacts/{target_id}", headers=headers)

    if response_delete.status_code == 200:
        logger.info(f"[DELETE УСПЕХ] Запрос на удаление прошел успешно (200 OK)")
    else:
        logger.error(f"[DELETE ОШИБКА] Сбой при удалении: {response_delete.status_code} - {response_delete.text}")
        pytest.fail("API не смог удалить контакт")

    # 3. ПРОВЕРКА: Убеждаемся, что контакт реально исчез из базы
    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_after = response_check.json().get("contacts", [])
    ids_after = [c.get("id") for c in contacts_after]

    assert target_id not in ids_after, "БАГ: Контакт не удалился из базы данных!"
    logger.info(f"[DELETE ПРОВЕРКА] Контакт {target_id} действительно исчез из базы!")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Delete All Contacts")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_api_clear_all_contacts(api_token):
    """Тест массового удаления контактов (Пылесос)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    response_clear = make_api_request("DELETE", f"{API_URL}/v1/contacts/clear", headers=headers)
    if response_clear.status_code == 200:
        logger.info("[CLEAR УСПЕХ] Запрос на массовое очищение выполнен")
    else:
        logger.error(f"[CLEAR ОШИБКА] Сбой массового удаления: {response_clear.status_code} - {response_clear.text}")
        pytest.fail("API не смог очистить базу")

    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_after = response_check.json().get("contacts", [])

    assert len(contacts_after) == 0, f"БАГ: База не пуста! Осталось {len(contacts_after)} контактов."
    logger.info("[CLEAR ПРОВЕРКА] Все контакты стерты в порошок. База девственно чиста!")