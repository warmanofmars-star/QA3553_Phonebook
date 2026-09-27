import allure
import pytest
from utils.logger import get_logger
from data.data_generator import ContactGenerator
from jsonschema import validate, ValidationError
from schemas.contact_schemas import GET_CONTACTS_RESPONSE_SCHEMA

logger = get_logger("API")

@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Get All Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_get_all_contacts(auth_api):
    contact = ContactGenerator.get_random_contact()
    auth_api.add_contact(contact.to_api_payload())

    response = auth_api.get_contacts()
    assert response.status_code == 200, f"Ошибка при получении контактов: {response.text}"

    try:
        validate(instance=response.json(), schema=GET_CONTACTS_RESPONSE_SCHEMA)
        logger.info("Контракт API (JSON Schema) успешно провалидирован!")
    except ValidationError as e:
        pytest.fail(f"Бэкенд нарушил контракт Swagger!\nОшибка структуры: {e.message}")

    contacts_list = response.json().get("contacts", [])
    all_phones = [c.get("phone") for c in contacts_list]

    assert contact.phone in all_phones, f"Созданный контакт с телефоном {contact.phone} не найден в базе!"
    logger.info(f"[GET УСПЕХ] Контакт найден. Всего записей: {len(contacts_list)}.")

@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Update Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_update_contact(auth_api):
    contact = ContactGenerator.get_random_contact()
    auth_api.add_contact(contact.to_api_payload())

    response_get = auth_api.get_contacts()
    contacts_list = response_get.json().get("contacts", [])

    target_id = next((c.get("id") for c in contacts_list if c.get("phone") == contact.phone), None)
    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    updated_payload = contact.to_api_payload()
    updated_payload["id"] = target_id
    updated_payload["name"] = "API_UPDATED_NAME"
    updated_payload["description"] = "This contact was updated via API"

    response_put = auth_api.update_contact(updated_payload)
    assert response_put.status_code == 200, f"Ошибка обновления: {response_put.text}"

    response_check = auth_api.get_contacts()
    contacts_list_after = response_check.json().get("contacts", [])

    updated_name_in_db = next((c.get("name") for c in contacts_list_after if c.get("id") == target_id), None)

    assert updated_name_in_db == "API_UPDATED_NAME", "Имя в базе данных не обновилось!"
    logger.info(f"[PUT УСПЕХ] Контакт {target_id} переименован в {updated_name_in_db}!")