import time
from pages.login_page import LoginPage

VALID_PASSWORD = "Mmar123456$"
EXISTING_EMAIL = "margo@gmail.com"

INVALID_EMAIL_FORMAT = "margogmail.com"
INVALID_PASSWORD_FORMAT = "12345"


def test_registration_success(driver):
    login_page = LoginPage(driver)
    login_page.open_login_form()

    unique_email = f"user_{time.time()}@gmail.com"

    login_page.fill_email(unique_email)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    assert login_page.is_logged()


def test_registration_existing_user_alert(driver):
    """Проверяем алерт 'User already exist' при регистрации существующего пользователя"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    # Сверяем текст с тем, что видим на скриншоте
    assert "User already exist" in login_page.get_alert_text()
    login_page.accept_alert()

def test_registration_invalid_format(driver):
    """Проверяем алерт с правилами валидации email/пароля"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    login_page.fill_email(INVALID_EMAIL_FORMAT)
    login_page.fill_password(INVALID_PASSWORD_FORMAT)
    login_page.submit_registration()

    # Проверяем только первую строчку из длинного алерта
    assert "Wrong email or password format" in login_page.get_alert_text()
    login_page.accept_alert()