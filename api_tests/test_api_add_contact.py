import allure
import os
import pytest
from utils.api_helper import make_api_request
from data.data_generator import ContactGenerator

API_URL = os.getenv("API_URL")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_add_contact(api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    contact = ContactGenerator.get_random_contact()

    # Супер-коротко: берем payload прямо из модели!
    contact_payload = contact.to_api_payload()

    response = make_api_request("POST", f"{API_URL}/v1/contacts", json=contact_payload, headers=headers)
    assert response.status_code == 200, f"Ошибка! Сервер вернул: {response.text}"
    print(f"\n[УСПЕХ] Контакт {contact.name} {contact.last_name} успешно создан!")


# Негативные тесты
@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact without Name")
@allure.severity(allure.severity_level.NORMAL)
def test_api_add_contact_missing_required_field(api_token):
    """Негативный тест: Создание контакта без обязательного поля (name)"""
    headers = {"Authorization": f"Bearer {api_token}"}
    contact = ContactGenerator.get_random_contact()

    # Берем полный payload и точечно удаляем из него ключ "name"
    contact_payload = contact.to_api_payload()
    del contact_payload["name"]

    response = make_api_request("POST", f"{API_URL}/v1/contacts", json=contact_payload, headers=headers)
    assert response.status_code == 400, f"БАГ БЭКЕНДА: Сервер принял контакт без имени! Статус: {response.status_code}"


@allure.epic("API Testing")
@allure.feature("Contacts Validation")
@allure.story("Create Duplicate Contact")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG BACKEND: Сервер возвращает 200 вместо 409 при дубликате (Swagger врет)")
def test_api_add_contact_duplicate(api_token):
    """Негативный тест: Попытка создать дубликат контакта"""
    headers = {"Authorization": f"Bearer {api_token}"}
    contact = ContactGenerator.get_random_contact()
    payload = contact.to_api_payload()

    # 1. Создаем оригинальный контакт
    res_first = make_api_request("POST", f"{API_URL}/v1/contacts", json=payload, headers=headers)
    assert res_first.status_code == 200, "Предусловие сломалось: первый контакт не создался"

    # 2. Пытаемся закинуть ТОТ ЖЕ САМЫЙ payload второй раз
    res_second = make_api_request("POST", f"{API_URL}/v1/contacts", json=payload, headers=headers)
    assert res_second.status_code == 409, f"БАГ БЭКЕНДА: Сервер позволил создать дубликат! Статус: {res_second.status_code}"