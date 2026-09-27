import allure
import pytest
import os
from data.data_generator import ContactGenerator
from utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'
logger = get_logger("API")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Delete Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_delete_contact(auth_api):
    contact = ContactGenerator.get_random_contact()
    auth_api.add_contact(contact.to_api_payload())

    response_get = auth_api.get_contacts()
    contacts_list = response_get.json().get("contacts", [])

    target_id = next((c.get("id") for c in contacts_list if c.get("phone") == contact.phone), None)
    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    response_delete = auth_api.delete_contact(target_id)

    if response_delete.status_code == 200:
        logger.info(f"[DELETE УСПЕХ] Запрос на удаление прошел успешно (200 OK)")
    else:
        logger.error(f"[DELETE ОШИБКА] Сбой при удалении: {response_delete.status_code} - {response_delete.text}")
        pytest.fail("API не смог удалить контакт")

    response_check = auth_api.get_contacts()
    ids_after = [c.get("id") for c in response_check.json().get("contacts", [])]

    assert target_id not in ids_after, "БАГ: Контакт не удалился из базы данных!"
    logger.info(f"[DELETE ПРОВЕРКА] Контакт {target_id} действительно исчез из базы!")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Delete All Contacts")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_api_clear_all_contacts(auth_api):
    response_clear = auth_api.clear_contacts()

    if response_clear.status_code == 200:
        logger.info("[CLEAR УСПЕХ] Запрос на массовое очищение выполнен")
    else:
        logger.error(f"[CLEAR ОШИБКА] Сбой массового удаления: {response_clear.status_code} - {response_clear.text}")
        pytest.fail("API не смог очистить базу")

    response_check = auth_api.get_contacts()
    contacts_after = response_check.json().get("contacts", [])

    assert len(contacts_after) == 0, f"БАГ: База не пуста! Осталось {len(contacts_after)} контактов."
    logger.info("[CLEAR ПРОВЕРКА] Все контакты стерты в порошок. База девственно чиста!")