import allure
import os
import pytest
from api.contact_api import PhonebookAPI
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
API_URL = os.getenv("API_URL")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")
logger = get_logger("API")


@allure.epic("API Testing")
@allure.feature("Authentication Controller")
@allure.story("Login Success")
@allure.severity(allure.severity_level.BLOCKER)
def test_api_login_success():
    """Позитивный тест: Успешная авторизация через API"""
    api = PhonebookAPI()
    response = api.login(USER_EMAIL, USER_PASSWORD)

    assert response.status_code == 200, f"Ошибка авторизации: {response.text}"
    token = response.json().get("token")
    assert token is not None, "Токен не пришел в ответе!"
    logger.info(f"[LOGIN УСПЕХ] Токен получен: {token[:15]}...")


@allure.epic("API Testing")
@allure.feature("Authentication Controller")
@allure.story("Login Negative")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("email, password, expected_status, scenario", [
    ("wrong_email@gmail.com", USER_PASSWORD, 401, "Несуществующий email"),
    (USER_EMAIL, "WrongPassword123!", 401, "Неверный пароль"),
])
def test_api_login_negative(email, password, expected_status, scenario):
    """Негативные тесты авторизации через API"""
    api = PhonebookAPI()
    response = api.login(email, password)

    assert response.status_code == expected_status, \
        f"Ожидали статус {expected_status} для сценария '{scenario}', но сервер вернул {response.status_code}"
    logger.info(f"[LOGIN NEGATIVE УСПЕХ] Сценарий '{scenario}' корректно отклонён со статусом {response.status_code}")