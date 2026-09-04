import os
import allure
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


@allure.severity(allure.severity_level.NORMAL)
def test_login_with_wrong_email(driver):
    """Негативный тест: Авторизация с неверным форматом email"""
    logger.info("--- ЗАПУСК ТЕСТА: test_login_with_wrong_email ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Запрашиваем юзера с битым email из генератора
    logger.info("ПОДГОТОВКА: Генерируем пользователя с невалидным email")
    bad_email_user = UserGenerator.get_user_with_invalid_email()

    logger.info(f"ШАГ 2: Вводим невалидный email: {bad_email_user.email}")
    login_page.fill_email(bad_email_user.email)
    login_page.fill_password(bad_email_user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Login")
    login_page.submit_login()

    logger.info("ПРОВЕРКА: Ожидаем Alert с текстом 'Wrong email or password'")
    assert "Wrong email or password" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при плохом email!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


@allure.severity(allure.severity_level.NORMAL)
def test_login_with_wrong_password(driver):
    """Негативный тест: Авторизация с неверным форматом пароля"""
    logger.info("--- ЗАПУСК ТЕСТА: test_login_with_wrong_password ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Запрашиваем юзера с битым паролем из генератора
    logger.info("ПОДГОТОВКА: Генерируем пользователя с невалидным password")
    bad_password_user = UserGenerator.get_user_with_invalid_password()

    # Используем валидный email (из .env) и невалидный сгенерированный пароль
    logger.info(f"ШАГ 2: Вводим валидный email и невалидный password: {bad_password_user.password}")
    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(bad_password_user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Login")
    login_page.submit_login()

    logger.info("ПРОВЕРКА: Ожидаем Alert с текстом 'Wrong email or password'")
    assert "Wrong email or password" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при плохом пароле!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


@allure.severity(allure.severity_level.NORMAL)
def test_login_unregistered_user(driver):
    """Негативный тест: Авторизация несуществующего пользователя"""
    logger.info("--- ЗАПУСК ТЕСТА: test_login_unregistered_user ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Запрашиваем уникального пользователя из генератора (его точно нет в базе)
    logger.info("ПОДГОТОВКА: Запрашиваем уникального пользователя из генератора (его точно нет в базе)")
    unregistered_user = UserGenerator.get_valid_user()

    logger.info(f"ШАГ 2: Авторизуемся под несуществующим юзером: {unregistered_user.email}")
    login_page.fill_email(unregistered_user.email)
    login_page.fill_password(unregistered_user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Login")
    login_page.submit_login()

    logger.info("ПРОВЕРКА: Ожидаем Alert с текстом 'Wrong email or password'")
    assert "Wrong email or password" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при несуществующем юзере!"
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


@allure.severity(allure.severity_level.NORMAL)
def test_registration_existing_user_alert(driver):
    """Негативный тест: Регистрация с уже существующим email в базе"""
    logger.info("--- ЗАПУСК ТЕСТА: test_registration_existing_user_alert ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Используем данные пользователя, который уже зарегистрирован
    logger.info(f"ПОДГОТОВКА/ШАГ 2: Вводим данные УЖЕ зарегистрированного пользователя: {EXISTING_EMAIL}")
    login_page.fill_email(EXISTING_EMAIL)
    login_page.fill_password(VALID_PASSWORD)

    logger.info("ШАГ 3: Нажимаем кнопку Registration")
    login_page.submit_registration()

    logger.info("ПРОВЕРКА: Ожидаем Alert с текстом 'User already exist'")
    assert "User already exist" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при дубликате пользователя!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


@allure.severity(allure.severity_level.NORMAL)
def test_registration_invalid_email_format(driver):
    """Негативный тест: Регистрация с невалидным email + ВАЛИДНЫМ паролем"""
    logger.info("--- ЗАПУСК ТЕСТА: test_registration_invalid_email_format ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Получаем пользователя с испорченным email из генератора
    logger.info("ПОДГОТОВКА: Получаем пользователя с испорченным email из генератора")
    bad_email_user = UserGenerator.get_user_with_invalid_email()

    logger.info(f"ШАГ 2: Вводим невалидный email: {bad_email_user.email}")
    login_page.fill_email(bad_email_user.email)
    login_page.fill_password(bad_email_user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Registration")
    login_page.submit_registration()

    logger.info("ПРОВЕРКА: Ожидаем Alert 'Wrong email or password format'")
    assert "Wrong email or password format" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при плохом email!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


@allure.severity(allure.severity_level.NORMAL)
def test_registration_invalid_password_format(driver):
    """Негативный тест: Регистрация с ВАЛИДНЫМ (уникальным) email + невалидным паролем"""
    logger.info("--- ЗАПУСК ТЕСТА: test_registration_invalid_password_format ---")
    login_page = LoginPage(driver)

    logger.info("ШАГ 1: Открываем страницу авторизации")
    login_page.open()

    # Получаем пользователя с испорченным паролем из генератора
    logger.info("ПОДГОТОВКА: Получаем пользователя с испорченным паролем из генератора")
    bad_password_user = UserGenerator.get_user_with_invalid_password()

    logger.info(f"ШАГ 2: Вводим невалидный пароль (email валидный): {bad_password_user.password}")
    login_page.fill_email(bad_password_user.email)
    login_page.fill_password(bad_password_user.password)

    logger.info("ШАГ 3: Нажимаем кнопку Registration")
    login_page.submit_registration()

    logger.info("ПРОВЕРКА: Ожидаем Alert 'Wrong email or password format'")
    assert "Wrong email or password format" in login_page.get_alert_text(), "Ошибка: Неверный текст Alert при плохом пароле!"
    login_page.accept_alert()
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")