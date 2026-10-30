"""
Утилита: выгружает все контакты постоянного пользователя (USER_EMAIL из .env)
в файл data/exported_contacts.json.

Запуск из корня проекта:
    python export_contacts.py

Использует тот же PhonebookAPI, что и тесты, поэтому получает те же
таймауты и логирование. Шаги Allure вне pytest просто ничего не делают.
"""

import json
import sys

from api.contact_api import PhonebookAPI
from config import PROJECT_ROOT, settings

# Путь строим от корня проекта, а не от текущей папки терминала
OUTPUT_FILE = PROJECT_ROOT / "data" / "exported_contacts.json"


def export_contacts_to_json() -> int:
    """Возвращает код выхода: 0 — успех, 1 — ошибка (удобно для скриптов и CI)."""
    if not settings.user_email or not settings.user_password:
        print("❌ Не заданы USER_EMAIL / USER_PASSWORD (см. .env.example)")
        return 1

    api = PhonebookAPI()

    print(f"Авторизация пользователя {settings.user_email}...")
    auth_response = api.login(settings.user_email, settings.user_password)
    if auth_response.status_code != 200:
        print(f"❌ Ошибка авторизации: {auth_response.status_code}. Проверьте данные в .env")
        return 1

    print("Загрузка списка контактов...")
    response = api.get_contacts()
    if response.status_code != 200:
        print(f"❌ Ошибка API при получении контактов: {response.status_code}")
        return 1

    contacts = response.json()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(contacts, indent=4, ensure_ascii=False), encoding="utf-8")

    count = len(contacts.get("contacts", []))
    print(f"✅ Успешно скачано {count} контактов в файл {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(export_contacts_to_json())
