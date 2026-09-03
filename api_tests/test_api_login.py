import allure
import os
from utils.api_helper import make_api_request
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Достаем базовый URL бэкенда и наши доступы
API_URL = os.getenv("API_URL")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")


@allure.epic("API Testing") # Глобальный раздел в отчете
@allure.feature("Contacts CRUD") # Подраздел
@allure.story("Login") # Название фичи
@allure.severity(allure.severity_level.BLOCKER) # Серьезность
def test_api_login_success():
    """Тест успешной авторизации через API и получения токена"""

    # 1. Формируем полный URL
    endpoint = f"{API_URL}/v1/user/login/usernamepassword"

    # 2. Формируем тело запроса (Payload) строго по документации
    payload = {
        "username": USER_EMAIL,
        "password": USER_PASSWORD
    }

    # 3. Делаем POST-запрос
    response = make_api_request("POST", endpoint, json=payload)

    # 4. Проверяем, что сервер ответил статусом 200 (OK)
    assert response.status_code == 200, f"Ошибка авторизации! Сервер вернул: {response.text}"

    # 5. Достаем токен из ответа
    token = response.json().get("token")

    # Проверяем, что токен не пустой
    assert token is not None, "Токен не пришел в ответе!"

    print(f"\n[УСПЕХ] Сервер выдал токен: {token[:15]}... (скрыто для безопасности)")