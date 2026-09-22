import allure
import os
import pytest
from utils.api_helper import make_api_request
from utils.logger import get_logger
from data.data_generator import ContactGenerator
from dotenv import load_dotenv

from jsonschema import validate, ValidationError
from schemas.contact_schemas import GET_CONTACTS_RESPONSE_SCHEMA

load_dotenv()
API_URL = os.getenv("API_URL")

# Подключаем логгер для API
logger = get_logger("API")

@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Get All Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_get_all_contacts(api_token):
    """Тест получения списка контактов (Read)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем уникальный контакт
    contact = ContactGenerator.get_random_contact()
    make_api_request("POST", f"{API_URL}/v1/contacts", json=contact.to_api_payload(), headers=headers)

    # 2. ШАГ ТЕСТА: Отправляем GET-запрос
    response = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    assert response.status_code == 200, f"Ошибка при получении контактов: {response.text}"

    # ==========================================
    # 🛠 СТРОГАЯ ВАЛИДАЦИЯ КОНТРАКТА (JSON SCHEMA)
    # ==========================================
    try:
        validate(instance=response.json(), schema=GET_CONTACTS_RESPONSE_SCHEMA)
        logger.info("Контракт API (JSON Schema) успешно провалидирован!")
    except ValidationError as e:
        pytest.fail(f"Бэкенд нарушил контракт Swagger!\nОшибка структуры: {e.message}")

    # ==========================================
    # 🎯 БИЗНЕС-ПРОВЕРКА (Наличие конкретных данных)
    # ==========================================
    contacts_list = response.json().get("contacts", [])
    all_phones = [c.get("phone") for c in contacts_list]


    assert contact.phone in all_phones, f"Созданный контакт с телефоном {contact.phone} не найден в базе!"
    print(f"\n[GET УСПЕХ] Контакт успешно найден в списке из {len(contacts_list)} записей.")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Update Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_update_contact(api_token):
    """Тест обновления существующего контакта (Update)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем контакт
    contact = ContactGenerator.get_random_contact()
    make_api_request("POST", f"{API_URL}/v1/contacts", json=contact.to_api_payload(), headers=headers)

    # 2. РАЗВЕДКА: Ищем ID
    response_get = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list = response_get.json().get("contacts", [])

    target_id = None
    for c in contacts_list:
        if c.get("phone") == contact.phone:
            target_id = c.get("id")
            break

    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    # 3. ШАГ ТЕСТА: Подготавливаем новые данные для обновления
    updated_payload = contact.to_api_payload()
    updated_payload["id"] = target_id  # Добавляем обязательный ID
    updated_payload["name"] = "API_UPDATED_NAME"  # Меняем имя
    updated_payload["description"] = "This contact was updated via API" # Меняем описание

    response_put = make_api_request("PUT", f"{API_URL}/v1/contacts", json=updated_payload, headers=headers)
    assert response_put.status_code == 200, f"Ошибка обновления: {response_put.text}"

    # 4. ПРОВЕРКА: Снова делаем GET
    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list_after = response_check.json().get("contacts", [])

    updated_name_in_db = None
    for c in contacts_list_after:
        if c.get("id") == target_id:
            updated_name_in_db = c.get("name")
            break

    assert updated_name_in_db == "API_UPDATED_NAME", "Имя в базе данных не обновилось!"
    print(f"\n[PUT УСПЕХ] Контакт {target_id} успешно переименован в {updated_name_in_db}!")