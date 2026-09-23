import os
import json
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения напрямую
load_dotenv()
API_URL = os.getenv("API_URL")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")


def export_contacts_to_json():
    print(f"Авторизация пользователя {USER_EMAIL}...")

    # 1. Получаем токен
    login_payload = {"username": USER_EMAIL, "password": USER_PASSWORD}
    auth_res = requests.post(f"{API_URL}/v1/user/login/usernamepassword", json=login_payload)

    if auth_res.status_code != 200:
        print(f"Ошибка авторизации: {auth_res.status_code}. Проверьте данные в .env")
        return

    token = auth_res.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    print("Загрузка списка контактов...")

    # 2. Запрашиваем контакты
    response = requests.get(f"{API_URL}/v1/contacts", headers=headers)

    if response.status_code == 200:
        contacts = response.json()

        # 3. Сохраняем в папку data
        os.makedirs("data", exist_ok=True)
        file_path = "data/exported_contacts.json"

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(contacts, file, indent=4, ensure_ascii=False)

        count = len(contacts.get("contacts", []))
        print(f"✅ Успешно скачано {count} контактов в файл {file_path}")
    else:
        print(f"❌ Ошибка API при получении контактов: {response.status_code}")


if __name__ == "__main__":
    export_contacts_to_json()