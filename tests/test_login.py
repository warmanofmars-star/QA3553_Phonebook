import os
import allure
import pytest
from pages.login_page import LoginPage
from data.data_generator import UserGenerator
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")

# ==========================================
# ТЕСТОВЫЕ ДАННЫЕ ДЛЯ АВТОРИЗАЦИИ (LOGIN)
# ==========================================
# Для тестов логина нам нужен пользователь, который уже точно есть в базе
# Достаем значения из переменных окружения
EXISTING_EMAIL = os.getenv("USER_EMAIL")
VALID_PASSWORD = os.getenv("USER_PASSWORD")


# ==========================================
# ТЕСТЫ НА АВТОРИЗАЦИЮ (LOGIN)
# ==========================================

@allure.severity(allure.severity_level.BLOCKER)
def test_login_success(driver):
    """Позитивный тест: Успешная авторизация с валидными данными"""
    logger.info("--- ЗАПУСК ТЕСТА: test_login_success ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    logger.info(f"ШАГ 2: Заполняем валидные данные пользователя: {EXISTING_EMAIL}")
    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)

    logger.info("ШАГ 3: Нажимаем кнопку Login")
    login_page.submit_login()

    logger.info("ПРОВЕРКА: Убеждаемся, что авторизация прошла успешно (появилась кнопка Sign Out)")
    assert login_page.is_logged(), "Ошибка: Пользователь не авторизовался!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# НЕГАТИВНЫЕ СЦЕНАРИИ
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("scenario_key, scenario_name", [
    ("invalid_email", "Невалидный формат email"),
    ("invalid_password", "Валидный email, но невалидный пароль"),
    ("unregistered", "Несуществующий пользователь")
])
def test_login_negative(driver, scenario_key, scenario_name):
    """Негативные тесты: Авторизация с неверными данными"""
    logger.info(f"--- ЗАПУСК ТЕСТА: test_login_negative ---")
    logger.info(f"СЦЕНАРИЙ: {scenario_name}")

    # 🛠 Генерируем данные внутри теста на основе ключа сценария
    if scenario_key == "invalid_email":
        user = UserGenerator.get_user_with_invalid_email()
        email, password = user.email, user.password
    elif scenario_key == "invalid_password":
        email = EXISTING_EMAIL
        password = UserGenerator.get_user_with_invalid_password().password
    elif scenario_key == "unregistered":
        user = UserGenerator.get_valid_user()
        email, password = user.email, user.password

    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    logger.info(f"ШАГ 2: Вводим данные -> Email: '{email}', Password: '{password}'")
    login_page.fill_email(email)
    login_page.fill_password(password)

    logger.info("ШАГ 3: Нажимаем кнопку Login")
    login_page.submit_login()

    logger.info("ПРОВЕРКА: Ожидаем Alert с текстом 'Wrong email or password'")
    assert "Wrong email or password" in login_page.get_alert_text(), f"Ошибка: Неверный текст Alert при сценарии '{scenario_name}'!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# ТЕСТЫ НА РЕГИСТРАЦИЮ (REGISTRATION)
# ==========================================

@allure.severity(allure.severity_level.BLOCKER)
def test_registration_success(driver):
    """Позитивный тест: Успешная регистрация нового пользователя"""
    logger.info("--- ЗАПУСК ТЕСТА: test_registration_success ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Получаем абсолютно нового уникального пользователя
    logger.info("ПОДГОТОВКА: Получаем абсолютно нового уникального пользователя")
    user = UserGenerator.get_valid_user()

    logger.info(f"ШАГ 2: Регистрируем нового юзера: {user.email}")
    login_page.fill_email(user.email)
    login_page.fill_password(user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Registration")
    login_page.submit_registration()

    # Проверяем, что после регистрации мы успешно авторизованы
    logger.info("ПРОВЕРКА: Убеждаемся, что после регистрации мы успешно авторизованы")
    assert login_page.is_logged(), "Ошибка: Пользователь не авторизовался после регистрации!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")

    # СОХРАНЯЕМ ДАННЫЕ В ФАЙЛ ДЛЯ ИСТОРИИ
    UserGenerator.save_user_credentials(user)
    logger.info(f"Данные пользователя {user.email} сохранены в data/valid_users.jsonl")


# НЕГАТИВНЫЕ СЦЕНАРИИ
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("scenario_key, expected_alert, scenario_name", [
    ("existing_user", "User already exist", "Регистрация уже существующего пользователя"),
    ("invalid_email", "Wrong email or password format", "Невалидный формат email"),
    ("invalid_password", "Wrong email or password format", "Невалидный формат пароля")
])
def test_registration_negative(driver, scenario_key, expected_alert, scenario_name):
    """Негативные тесты: Регистрация с неверными данными или существующим email"""
    logger.info(f"--- ЗАПУСК ТЕСТА: test_registration_negative ---")
    logger.info(f"СЦЕНАРИЙ: {scenario_name}")

    # 🛠 Генерируем данные внутри теста на основе ключа сценария
    if scenario_key == "existing_user":
        email = EXISTING_EMAIL
        password = UserGenerator.get_valid_user().password
    elif scenario_key == "invalid_email":
        user = UserGenerator.get_user_with_invalid_email()
        email, password = user.email, user.password
    elif scenario_key == "invalid_password":
        email = UserGenerator.get_valid_user().email
        password = UserGenerator.get_user_with_invalid_password().password

    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации/регистрации")
    login_page.open()

    logger.info(f"ШАГ 2: Вводим данные -> Email: '{email}', Password: '{password}'")
    login_page.fill_email(email)
    login_page.fill_password(password)

    logger.info("ШАГ 3: Нажимаем кнопку Registration")
    login_page.submit_registration()

    logger.info(f"ПРОВЕРКА: Ожидаем Alert с текстом '{expected_alert}'")
    actual_alert_text = login_page.get_alert_text()

    assert expected_alert in actual_alert_text, \
        f"Ошибка при сценарии '{scenario_name}': Ожидали '{expected_alert}', но получили '{actual_alert_text}'!"

    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")