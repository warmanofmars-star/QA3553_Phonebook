import allure
import pytest
import os
from utils.api_helper import make_api_request
from data.data_generator import ContactGenerator
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")
# Читаем состояние тумблера из .env
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'

@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Delete Contact") # Название фичи
@allure.severity(allure.severity_level.CRITICAL) # Серьезность
def test_api_delete_contact(api_token):
    """Тест удаления конкретного контакта (Delete)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем контакт и узнаем его ID
    contact = ContactGenerator.get_random_contact()
    payload = {
        "name": contact.name,
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": contact.description
    }
    make_api_request("POST", f"{API_URL}/v1/contacts", json=payload, headers=headers)

    response_get = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list = response_get.json().get("contacts", [])

    target_id = None
    for c in contacts_list:
        if c.get("phone") == contact.phone:
            target_id = c.get("id")
            break

    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    # 2. ШАГ ТЕСТА: Удаляем контакт по ID
    # Обрати внимание на URL: мы передаем target_id прямо в адресную строку
    response_delete = make_api_request("DELETE", f"{API_URL}/v1/contacts/{target_id}", headers=headers)
    assert response_delete.status_code == 200, f"Ошибка удаления: {response_delete.text}"

    # 3. ПРОВЕРКА: Убеждаемся, что контакт реально исчез из базы
    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_after = response_check.json().get("contacts", [])

    # Собираем список всех ID, которые остались в базе
    ids_after = [c.get("id") for c in contacts_after]

    assert target_id not in ids_after, "БАГ: Контакт не удалился из базы данных!"
    print(f"\n[DELETE УСПЕХ] Контакт {target_id} успешно удален!")

@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Delete All Contacts") # Название фичи
@allure.severity(allure.severity_level.CRITICAL) # Серьезность
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_api_clear_all_contacts(api_token):
    """Тест массового удаления контактов (Пылесос)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ШАГ ТЕСТА: Вызываем эндпоинт полной очистки
    response_clear = make_api_request("DELETE", f"{API_URL}/v1/contacts/clear", headers=headers)
    assert response_clear.status_code == 200, f"Ошибка массового удаления: {response_clear.text}"

    # 2. ПРОВЕРКА: Запрашиваем список и убеждаемся, что он абсолютно пуст
    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_after = response_check.json().get("contacts", [])

    assert len(contacts_after) == 0, f"БАГ: База не пуста! Осталось {len(contacts_after)} контактов."
    print(f"\n[CLEAR УСПЕХ] Все 127+ контактов стерты в порошок. База девственно чиста!")