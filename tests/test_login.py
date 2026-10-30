"""
Вход и регистрация через UI.

Все тесты используют временных пользователей (temp_user), а не постоянный
аккаунт из .env: тесты не зависят от чужих данных и работают где угодно,
даже без USER_EMAIL/USER_PASSWORD.
Тексты ошибок — из SRS (F1–F4), а не из фактического поведения приложения.
"""

import allure
import pytest

from data.data_generator import UserGenerator
from data.known_bugs import known_bug
from pages.login_page import LoginPage

pytestmark = [pytest.mark.ui, allure.epic("UI Testing"), allure.feature("Authentication")]

WRONG_CREDENTIALS = "Wrong email or password"   # SRS F1, F2, F4
USER_ALREADY_EXISTS = "User already exists"     # SRS F3


def _expect_alert(page: LoginPage, expected: str) -> None:
    """Проверка: появился Alert, и в нём текст из требования."""
    alert_text = page.wait_for_alert_text()
    assert alert_text is not None, f"Alert не появился (ожидался текст '{expected}')"
    assert expected in alert_text, f"Ожидался текст '{expected}', получено: '{alert_text}'"
    page.accept_alert()


# ==========================================
# ВХОД
# ==========================================
@pytest.mark.smoke
@allure.story("Login success")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("TC-0006")
def test_login_success(driver, temp_user):
    login_page = LoginPage(driver)
    login_page.open()
    login_page.login(temp_user.user.email, temp_user.user.password)

    assert login_page.is_signed_in(), "Пользователь не авторизовался: нет кнопки Sign Out"


@pytest.mark.regression
@allure.story("Login negative")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("scenario, test_case", [
    pytest.param("invalid_email", "TC-0007", id="TC-0007-invalid-email"),
    pytest.param("wrong_password", "TC-0008", id="TC-0008-wrong-password"),
    pytest.param("unregistered", "TC-0009", id="TC-0009-unregistered-user"),
])
def test_login_negative(driver, temp_user, scenario, test_case):
    allure.dynamic.tag(test_case)
    credentials = {
        "invalid_email": (UserGenerator.get_user_with_invalid_email().email, temp_user.user.password),
        "wrong_password": (temp_user.user.email, UserGenerator.generate_valid_password()),
        "unregistered": (UserGenerator.get_valid_user().email, UserGenerator.generate_valid_password()),
    }
    email, password = credentials[scenario]

    login_page = LoginPage(driver)
    login_page.open()
    login_page.login(email, password)

    _expect_alert(login_page, WRONG_CREDENTIALS)
    assert not login_page.is_signed_in(timeout=1), "Пользователь авторизовался с неверными данными"


# ==========================================
# РЕГИСТРАЦИЯ
# ==========================================
@pytest.mark.smoke
@allure.story("Registration success")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("TC-0001")
def test_registration_success(driver):
    user = UserGenerator.get_valid_user()

    login_page = LoginPage(driver)
    login_page.open()
    login_page.register(user.email, user.password)

    assert login_page.is_signed_in(), "Пользователь не авторизовался после регистрации"


@pytest.mark.regression
@allure.story("Registration negative")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("scenario, expected_alert, test_case", [
    pytest.param("invalid_email", WRONG_CREDENTIALS, "TC-0002", id="TC-0002-invalid-email"),
    pytest.param("invalid_password", WRONG_CREDENTIALS, "TC-0003", id="TC-0003-invalid-password"),
    pytest.param("existing_user", USER_ALREADY_EXISTS, "TC-0004", id="TC-0004-existing-user",
                 marks=known_bug("USER_EXISTS_WORDING")),
    pytest.param("existing_email", USER_ALREADY_EXISTS, "TC-0005", id="TC-0005-existing-email-new-password",
                 marks=known_bug("USER_EXISTS_WORDING")),
])
def test_registration_negative(driver, temp_user, scenario, expected_alert, test_case):
    allure.dynamic.tag(test_case)
    credentials = {
        "invalid_email": (UserGenerator.get_user_with_invalid_email().email, UserGenerator.generate_valid_password()),
        "invalid_password": (UserGenerator.get_valid_user().email, UserGenerator.get_user_with_invalid_password().password),
        "existing_user": (temp_user.user.email, temp_user.user.password),
        "existing_email": (temp_user.user.email, UserGenerator.generate_valid_password()),
    }
    email, password = credentials[scenario]

    login_page = LoginPage(driver)
    login_page.open()
    login_page.register(email, password)

    _expect_alert(login_page, expected_alert)
