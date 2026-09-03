import allure
import os
from utils.api_helper import make_api_request
from data.data_generator import ContactGenerator
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")


@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Get All Contact") # Название фичи
@allure.severity(allure.severity_level.CRITICAL) # Серьезность
def test_api_get_all_contacts(api_token):
    """Тест получения списка контактов (Read)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем уникальный контакт
    contact = ContactGenerator.get_random_contact()
    payload = {
        "name": contact.name,
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": contact.description
    }
    make_api_request("POST",f"{API_URL}/v1/contacts", json=payload, headers=headers)

    # 2. ШАГ ТЕСТА: Отправляем GET-запрос на получение всех контактов
    # Обрати внимание: для GET-запроса не нужно тело (json), только заголовки!
    response = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)

    assert response.status_code == 200, f"Ошибка при получении контактов: {response.text}"

    # 3. Парсим ответ: сервер возвращает словарь {"contacts": [список контактов]}
    # Метод .get("contacts", []) вернет пустой список, если ключа вдруг не окажется
    contacts_list = response.json().get("contacts", [])

    # 4. ПРОВЕРКА: Ищем наш уникальный телефон в полученном списке
    # Вытаскиваем все телефоны в один список с помощью генератора
    all_phones = [c.get("phone") for c in contacts_list]

    assert contact.phone in all_phones, f"Созданный контакт с телефоном {contact.phone} не найден в базе!"
    print(f"\n[GET УСПЕХ] Контакт успешно найден в списке из {len(contacts_list)} записей.")

@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Update Contact") # Название фичи
@allure.severity(allure.severity_level.CRITICAL) # Серьезность
def test_api_update_contact(api_token):
    """Тест обновления существующего контакта (Update)"""
    headers = {"Authorization": f"Bearer {api_token}"}

    # 1. ПРЕДУСЛОВИЕ: Создаем контакт
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

    # 2. РАЗВЕДКА: Делаем GET-запрос, чтобы найти ID этого контакта
    response_get = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list = response_get.json().get("contacts", [])

    # Ищем контакт по нашему уникальному телефону и забираем его id
    target_id = None
    for c in contacts_list:
        if c.get("phone") == contact.phone:
            target_id = c.get("id")
            break

    assert target_id is not None, "Не удалось найти ID созданного контакта!"

    # 3. ШАГ ТЕСТА: Подготавливаем новые данные для обновления
    # Меняем имя и описание, остальное оставляем старым
    updated_payload = {
        "id": target_id,  # КРИТИЧЕСКИ ВАЖНОЕ ПОЛЕ ДЛЯ PUT
        "name": "API_UPDATED_NAME",  # Изменили
        "lastName": contact.last_name,
        "phone": contact.phone,
        "email": contact.email,
        "address": contact.address,
        "description": "This contact was updated via API"  # Изменили
    }

    # Отправляем PUT-запрос
    response_put = make_api_request("PUT", f"{API_URL}/v1/contacts", json=updated_payload, headers=headers)
    assert response_put.status_code == 200, f"Ошибка обновления: {response.text}"

    # 4. ПРОВЕРКА: Снова делаем GET и проверяем, что имя реально изменилось
    response_check = make_api_request("GET", f"{API_URL}/v1/contacts", headers=headers)
    contacts_list_after = response_check.json().get("contacts", [])

    updated_name_in_db = None
    for c in contacts_list_after:
        if c.get("id") == target_id:
            updated_name_in_db = c.get("name")
            break

    assert updated_name_in_db == "API_UPDATED_NAME", "Имя в базе данных не обновилось!"
    print(f"\n[PUT УСПЕХ] Контакт {target_id} успешно переименован в {updated_name_in_db}!")