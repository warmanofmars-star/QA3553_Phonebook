from pages.login_page import LoginPage
from data.data_generator import UserGenerator
import os
from dotenv import load_dotenv

# ==========================================
# ТЕСТОВЫЕ ДАННЫЕ ДЛЯ АВТОРИЗАЦИИ (LOGIN)
# ==========================================
# Для тестов логина нам нужен пользователь, который уже точно есть в базе
# Загружаем переменные из файла .env
load_dotenv()

# Достаем значения из переменных окружения
EXISTING_EMAIL = os.getenv("USER_EMAIL")
VALID_PASSWORD = os.getenv("USER_PASSWORD")

INVALID_EMAIL_FORMAT = "margogmail.com"
INVALID_PASSWORD_FORMAT = "12345"


# ==========================================
# ТЕСТЫ НА АВТОРИЗАЦИЮ (LOGIN)
# ==========================================

def test_login_success(driver):
    """Позитивный тест: Успешная авторизация с валидными данными"""
    login_page = LoginPage(driver)
    login_page.open()

    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    assert login_page.is_logged()


def test_login_with_wrong_email(driver):
    """Негативный тест: Авторизация с неверным форматом email"""
    login_page = LoginPage(driver)
    login_page.open()

    login_page.fill_email(INVALID_EMAIL_FORMAT)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


def test_login_with_wrong_password(driver):
    """Негативный тест: Авторизация с неверным форматом пароля"""
    login_page = LoginPage(driver)
    login_page.open()

    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(INVALID_PASSWORD_FORMAT)
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


def test_login_unregistered_user(driver):
    """Негативный тест: Авторизация несуществующего пользователя"""
    login_page = LoginPage(driver)
    login_page.open()

    # Запрашиваем уникального пользователя из генератора (его точно нет в базе)
    unregistered_user = UserGenerator.get_valid_user()

    login_page.fill_email(unregistered_user.email)
    login_page.fill_password(unregistered_user.password)
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


# ==========================================
# ТЕСТЫ НА РЕГИСТРАЦИЮ (REGISTRATION)
# ==========================================

def test_registration_success(driver):
    """Позитивный тест: Успешная регистрация нового пользователя"""
    login_page = LoginPage(driver)
    login_page.open()

    # Получаем абсолютно нового уникального пользователя
    user = UserGenerator.get_valid_user()

    login_page.fill_email(user.email)
    login_page.fill_password(user.password)
    login_page.submit_registration()

    # Проверяем, что после регистрации мы успешно авторизованы
    assert login_page.is_logged()


def test_registration_existing_user_alert(driver):
    """Негативный тест: Регистрация с уже существующим email в базе"""
    login_page = LoginPage(driver)
    login_page.open()

    # Используем данные пользователя, который уже зарегистрирован
    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    assert "User already exist" in login_page.get_alert_text()
    login_page.accept_alert()


def test_registration_invalid_email_format(driver):
    """Негативный тест: Регистрация с невалидным email + ВАЛИДНЫМ паролем"""
    login_page = LoginPage(driver)
    login_page.open()

    # Получаем пользователя с испорченным email из генератора
    bad_email_user = UserGenerator.get_user_with_invalid_email()

    login_page.fill_email(bad_email_user.email)
    login_page.fill_password(bad_email_user.password)
    login_page.submit_registration()

    assert "Wrong email or password format" in login_page.get_alert_text()
    login_page.accept_alert()


def test_registration_invalid_password_format(driver):
    """Негативный тест: Регистрация с ВАЛИДНЫМ (уникальным) email + невалидным паролем"""
    login_page = LoginPage(driver)
    login_page.open()

    # Получаем пользователя с испорченным паролем из генератора
    bad_password_user = UserGenerator.get_user_with_invalid_password()

    login_page.fill_email(bad_password_user.email)
    login_page.fill_password(bad_password_user.password)
    login_page.submit_registration()

    assert "Wrong email or password format" in login_page.get_alert_text()
    login_page.accept_alert()