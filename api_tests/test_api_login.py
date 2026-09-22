import allure
import os
import pytest
from utils.api_helper import make_api_request
from dotenv import load_dotenv
from utils.logger import get_logger

# Загружаем переменные окружения
load_dotenv()

# Достаем базовый URL бэкенда и наши доступы
API_URL = os.getenv("API_URL")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")

logger = get_logger("API")


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

    if response.status_code == 200:
        token = response.json().get("token")
        assert token is not None, "Токен не пришел в ответе!"
        logger.info(f"[LOGIN УСПЕХ] Сервер выдал токен: {token[:15]}... (скрыто для безопасности)")
    else:
        logger.error(f"[LOGIN ОШИБКА] Сбой авторизации: {response.status_code} - {response.text}")
        pytest.fail("API не смог авторизовать пользователя")