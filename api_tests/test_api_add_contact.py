import allure
import os
import requests
import pytest
from data.data_generator import ContactGenerator

API_URL = os.getenv("API_URL")


@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Create Contact") # Название фичи
@allure.severity(allure.severity_level.CRITICAL) # Серьезность
# Пробрасываем нашу новую фикстуру в скобки
def test_api_add_contact(api_token):
    # ==========================================
    # ШАГ 1: Подготавливаем Заголовки (Headers)
    # ==========================================
    # Используем готовый токен из фикстуры!
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    # ==========================================
    # ШАГ 2: Генерируем данные и форматируем под API
    # ==========================================
    contact = ContactGenerator.get_random_contact()

    contact_payload = {
        "name": contact.name,
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": contact.description
    }

    # ==========================================
    # ШАГ 3: Отправляем запрос на создание
    # ==========================================
    response = requests.post(f"{API_URL}/v1/contacts", json=contact_payload, headers=headers)

    # ==========================================
    # ПРОВЕРКИ
    # ==========================================
    assert response.status_code == 200, f"Ошибка! Сервер вернул: {response.text}"

    print(f"\n[УСПЕХ] Контакт {contact.name} {contact.last_name} успешно создан!")



#Негативные тесты
@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact without Name")
@allure.severity(allure.severity_level.NORMAL)
def test_api_add_contact_missing_required_field(api_token):
    """Негативный тест: Создание контакта без обязательного поля (name)"""
    headers = {"Authorization": f"Bearer {api_token}"}
    contact = ContactGenerator.get_random_contact()

    # Собираем payload, но СПЕЦИАЛЬНО "забываем" передать поле name
    contact_payload = {
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": contact.description
    }

    response = requests.post(f"{API_URL}/v1/contacts", json=contact_payload, headers=headers)

    # По спецификации Swagger сервер должен отбить запрос со статусом 400 (Bad Request)
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

    payload = {
        "name": contact.name,
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": contact.description
    }

    # 1. Создаем оригинальный контакт
    res_first = requests.post(f"{API_URL}/v1/contacts", json=payload, headers=headers)
    assert res_first.status_code == 200, "Предусловие сломалось: первый контакт не создался"

    # 2. Пытаемся закинуть ТОТ ЖЕ САМЫЙ payload второй раз
    res_second = requests.post(f"{API_URL}/v1/contacts", json=payload, headers=headers)

    # По Swagger сервер должен выдать ошибку 409 (Conflict) - Duplicate contact fields
    assert res_second.status_code == 409, f"БАГ БЭКЕНДА: Сервер позволил создать дубликат! Статус: {res_second.status_code}"