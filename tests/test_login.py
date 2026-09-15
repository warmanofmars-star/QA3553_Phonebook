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


#НЕГАТИВНЫЕ СЦЕНАРИИ
# Заранее генерируем данные для негативных сценариев
bad_email_user = UserGenerator.get_user_with_invalid_email()
bad_password_user = UserGenerator.get_user_with_invalid_password()
unregistered_user = UserGenerator.get_valid_user()
valid_user = UserGenerator.get_valid_user()


@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("email, password, scenario_name", [
    (bad_email_user.email, bad_email_user.password, "Невалидный формат email"),
    (EXISTING_EMAIL, bad_password_user.password, "Валидный email, но невалидный пароль"),
    (unregistered_user.email, unregistered_user.password, "Несуществующий пользователь")
])


def test_login_negative(driver, email, password, scenario_name):
    """Негативные тесты: Авторизация с неверными данными"""
    logger.info(f"--- ЗАПУСК ТЕСТА: test_login_negative ---")
    logger.info(f"СЦЕНАРИЙ: {scenario_name}")

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


#НЕГАТИВНЫЕ СЦЕНАРИИ
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("email, password, expected_alert, scenario_name", [
    # 1. Сценарий: Пользователь уже существует (используем EXISTING_EMAIL из окружения)
    (EXISTING_EMAIL, valid_user.password, "User already exist", "Регистрация уже существующего пользователя"),

    # 2. Сценарий: Сломанный email (формат)
    (bad_email_user.email, bad_email_user.password, "Wrong email or password format", "Невалидный формат email"),

    # 3. Сценарий: Сломанный пароль (короткий)
    (valid_user.email, bad_password_user.password, "Wrong email or password format", "Невалидный формат пароля")
])
def test_registration_negative(driver, email, password, expected_alert, scenario_name):
    """Негативные тесты: Регистрация с неверными данными или существующим email"""
    logger.info(f"--- ЗАПУСК ТЕСТА: test_registration_negative ---")
    logger.info(f"СЦЕНАРИЙ: {scenario_name}")

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