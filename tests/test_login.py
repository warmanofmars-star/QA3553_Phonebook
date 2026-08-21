import time
from pages.login_page import LoginPage

# --- ТЕСТОВЫЕ ДАННЫЕ ---

VALID_EMAIL = "margo@gmail.com"
VALID_PASSWORD = "Mmar123456$"

INVALID_EMAIL = "margogmail.com"
INVALID_PASSWORD = "12345"


# ==========================================
# ТЕСТЫ НА АВТОРИЗАЦИЮ (LOGIN)
# ==========================================

def test_login_success(driver):
    """Позитивный тест: Успешная авторизация с валидными данными"""
    login_page = LoginPage(driver)
    login_page.open_login_form()
    login_page.fill_email(VALID_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    assert login_page.is_logged()


def test_login_with_wrong_email(driver):
    """Негативный тест: Авторизация с неверным форматом email"""
    login_page = LoginPage(driver)
    login_page.open_login_form()
    login_page.fill_email(INVALID_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


def test_login_with_wrong_password(driver):
    """Негативный тест: Авторизация с неверным форматом пароля"""
    login_page = LoginPage(driver)
    login_page.open_login_form()
    login_page.fill_email(VALID_EMAIL)
    login_page.fill_password(INVALID_PASSWORD)
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


def test_login_unregistered_user(driver):
    """Негативный тест: Авторизация несуществующего пользователя"""
    login_page = LoginPage(driver)
    login_page.open_login_form()
    login_page.fill_email("margomar@gmail.com")
    login_page.fill_password("Mma6595623$")
    login_page.submit_login()

    assert "Wrong email or password" in login_page.get_alert_text()
    login_page.accept_alert()


# ==========================================
# ТЕСТЫ НА РЕГИСТРАЦИЮ (REGISTRATION)
# ==========================================

def test_registration_success(driver):
    """Позитивный тест: Успешная регистрация нового пользователя"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    # Генерируем уникальный email для каждого прогона
    unique_email = f"user_{time.time()}@gmail.com"

    login_page.fill_email(unique_email)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    # Проверяем, что после регистрации мы успешно авторизованы
    assert login_page.is_logged()


def test_registration_existing_user_alert(driver):
    """Негативный тест: Регистрация с уже существующим email в базе"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    login_page.fill_email(VALID_EMAIL)  # Используем существующий email
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    assert "User already exist" in login_page.get_alert_text()
    login_page.accept_alert()


def test_registration_invalid_email_format(driver):
    """Негативный тест: Регистрация с невалидным email + ВАЛИДНЫМ паролем"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    login_page.fill_email(INVALID_EMAIL)
    login_page.fill_password(VALID_PASSWORD)
    login_page.submit_registration()

    assert "Wrong email or password format" in login_page.get_alert_text()
    login_page.accept_alert()


def test_registration_invalid_password_format(driver):
    """Негативный тест: Регистрация с ВАЛИДНЫМ (уникальным) email + невалидным паролем"""
    login_page = LoginPage(driver)
    login_page.open_login_form()

    # Генерируем уникальный email, чтобы система проверяла именно пароль, а не ругалась на дубликат
    unique_email = f"user_{time.time()}@gmail.com"

    login_page.fill_email(unique_email)
    login_page.fill_password(INVALID_PASSWORD)
    login_page.submit_registration()

    assert "Wrong email or password format" in login_page.get_alert_text()
    login_page.accept_alert()