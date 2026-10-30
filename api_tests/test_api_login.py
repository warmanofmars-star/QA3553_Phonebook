import allure
import pytest
from api.contact_api import PhonebookAPI
from utils.validators import assert_secure_error
from utils.logger import get_logger

logger = get_logger("API")


@pytest.mark.smoke
@pytest.mark.api
@allure.epic("API Testing")
@allure.feature("Authentication Controller")
@allure.story("Login Success")
@allure.severity(allure.severity_level.BLOCKER)
def test_api_login_success(temp_user):
    """Позитивный тест: Успешная авторизация через API (Sandbox)"""
    user = temp_user["user"]
    api = PhonebookAPI()

    response = api.login(user.email, user.password)

    assert response.status_code == 200, f"Ошибка авторизации: {response.text}"
    token = response.json().get("token")
    assert token is not None, "Токен не пришел в ответе!"
    logger.info("[LOGIN УСПЕХ] Токен получен")  # сам токен в лог не пишем


@pytest.mark.regression
@pytest.mark.api
@allure.epic("API Testing")
@allure.feature("Authentication Controller")
@allure.story("Login Negative")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("scenario_key, expected_status, scenario", [
    ("wrong_email", 401, "Несуществующий email"),
    ("wrong_password", 401, "Неверный пароль"),
])
def test_api_login_negative(temp_user, scenario_key, expected_status, scenario):
    """Негативные тесты авторизации через API без утечки пароля в параметры отчета"""
    user = temp_user["user"]
    api = PhonebookAPI()

    if scenario_key == "wrong_email":
        email, password = "wrong_unregistered_email@gmail.com", user.password
    else:
        email, password = user.email, "WrongPassword123!"

    response = api.login(email, password)

    assert_secure_error(response, expected_status)
    logger.info(f"[LOGIN NEGATIVE УСПЕХ] Сценарий '{scenario}' корректно отклонён со статусом {response.status_code}")