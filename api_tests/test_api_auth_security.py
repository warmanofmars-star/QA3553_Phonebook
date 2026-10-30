import pytest
import allure
from api.contact_api import PhonebookAPI
from utils.validators import assert_secure_error
from utils.logger import get_logger
from data.known_bugs import known_bug

logger = get_logger("API_SECURITY")
pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.regression]


@allure.epic("API Security")
@allure.feature("Authentication")
@allure.story("Check Token Validation")
@pytest.mark.parametrize("auth_header, expected_status, scenario", [
    pytest.param(
        None, 401, "Запрос вообще без заголовка Authorization",
        marks=known_bug("NO_AUTH_403"),
    ),
    ("Bearer ", 401, "Заголовок есть, но токен пустой"),
    ("Bearer invalid_token_12345", 401, "Абсолютно невалидный токен"),
    ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", 401, "Синтаксически похожий, но фейковый JWT"),
    ("Basic dXNlcjpwYXNzd29yZA==", 401, "Подмена схемы (Basic вместо Bearer)")
])
def test_api_invalid_tokens(auth_header, expected_status, scenario):
    """Проверка 14: Запрос без валидной аутентификации должен быть отклонен"""
    logger.info(f"--- СЦЕНАРИЙ: {scenario} ---")

    headers = {"Authorization": auth_header} if auth_header is not None else {}

    with allure.step(f"Отправка GET /contacts с кривым токеном: {scenario}"):
        # Новый клиент без логина: в его сессии нет нашего токена,
        # поэтому уходит ровно тот заголовок Authorization, который мы проверяем
        response = PhonebookAPI().request("GET", "/v1/contacts", headers=headers)

    # Вызываем наш мега-валидатор! Он проверит и 401 статус, и отсутствие утечек.
    assert_secure_error(response, expected_status)