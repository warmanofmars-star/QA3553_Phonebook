import pytest
import allure
from models.contact import Contact
from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator
from selenium.common.exceptions import TimeoutException
from data.test_data import load_contact_data_from_csv
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================
@allure.severity(allure.severity_level.CRITICAL)
def test_add_contact_success_all_fields(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_add_contact_success_all_fields ---")

    # 1. Инициализируем страницу
    contact_page = ContactPage(authenticated_driver)

    # 2. Открываем форму добавления контакта
    logger.info("ШАГ 1: Открываем страницу добавления контакта (вкладка ADD)")
    contact_page.open()

    # 3. Генерируем уникальные тестовые данные через Faker
    logger.info("ПОДГОТОВКА: Генерируем уникальные тестовые данные нового контакта")
    contact = ContactGenerator.get_random_contact()

    # 4. Заполняем форму и сохраняем
    logger.info(f"ШАГ 2: Заполняем форму данными: {contact.name} {contact.last_name}")
    contact_page.fill_contact_form(contact)

    logger.info("ШАГ 3: Нажимаем кнопку Save")
    contact_page.submit_contact()

    # 5. ПРОВЕРКА: убеждаемся, что карточка с нужным телефоном появилась в списке.
    logger.info(f"ПРОВЕРКА: Убеждаемся, что карточка с телефоном {contact.phone} появилась в списке")
    assert contact_page.is_contact_card_visible(contact.phone), \
        f"Ошибка: Карточка контакта с телефоном {contact.phone} не появилась в списке!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ (Данные берутся из CSV)
# ==========================================

@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("name, last_name, phone, email, address, description, expected_error",
                         load_contact_data_from_csv())
def test_add_contact_negative(authenticated_driver, name, last_name, phone, email, address, description,
                              expected_error):
    logger.info(f"--- ЗАПУСК ТЕСТА: test_add_contact_negative (Данные: phone='{phone}', email='{email}') ---")

    contact_page = ContactPage(authenticated_driver)
    logger.info("ШАГ 1: Открываем страницу добавления контакта")
    contact_page.open()

    logger.info("ПОДГОТОВКА: Формируем модель контакта с невалидными данными из CSV")
    invalid_contact = Contact(
        name=name,
        last_name=last_name,
        phone=phone,
        email=email,
        address=address,
        description=description
    )

    logger.info("ШАГ 2: Заполняем форму и нажимаем Save")
    contact_page.fill_contact_form(invalid_contact)
    contact_page.submit_contact()

    try:
        logger.info(f"ПРОВЕРКА 1: Ожидаем появление Alert с текстом: '{expected_error}'")
        alert_text = contact_page.get_alert_text()
        assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"

        logger.info(f"Успешно получен ожидаемый Alert: '{alert_text}'")
        contact_page.accept_alert()
    except TimeoutException:
        logger.error(f"БАГ ПРИЛОЖЕНИЯ: Ожидаемый Alert '{expected_error}' так и не появился!")
        pytest.fail(f"БАГ ПРИЛОЖЕНИЯ: Ожидаемый Alert с текстом '{expected_error}' так и не появился!")

    logger.info("ПРОВЕРКА 2: Вкладка ADD должна оставаться активной")
    assert contact_page.is_add_tab_active(), "Вкладка ADD должна оставаться активной после попытки сохранить невалидный контакт!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG: Система позволяет создавать дубликаты по номеру телефона без Alert")
def test_add_contact_duplicate_phone(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_add_contact_duplicate_phone ---")
    contact_page = ContactPage(authenticated_driver)

    # --- ШАГ 1: Создаем первый уникальный контакт ---
    logger.info("ШАГ 1: Создаем первый оригинальный контакт")
    contact_page.open()
    first_contact = ContactGenerator.get_random_contact()
    contact_page.fill_contact_form(first_contact)
    contact_page.submit_contact()

    # --- ШАГ 2: Пытаемся создать второй контакт с ТЕМ ЖЕ номером ---
    logger.info(f"ШАГ 2: Пытаемся создать дубликат с ТЕМ ЖЕ номером телефона: {first_contact.phone}")
    contact_page.open()
    duplicate_contact = ContactGenerator.get_random_contact()
    duplicate_contact.phone = first_contact.phone  # Копируем телефон из первого контакта!

    contact_page.fill_contact_form(duplicate_contact)
    contact_page.submit_contact()

    # --- ШАГ 3: Проверяем реакцию системы ---
    logger.info("ПРОВЕРКА: Ожидаем появление Alert об ошибке дубликата")
    try:
        alert_text = contact_page.get_alert_text()
        logger.warning(f"[РАЗВЕДКА] УРА! Система выдала Alert: '{alert_text}'")
        contact_page.accept_alert()
        # Пока ставим заглушку, чтобы тест прошел, если алерт есть
        assert True
    except TimeoutException:
        logger.error("БАГ ПРИЛОЖЕНИЯ: Alert о дубликате телефона так и не появился! Контакт-клон сохранен.")
        pytest.fail("БАГ ПРИЛОЖЕНИЯ: Alert о дубликате телефона так и не появился! Контакт-клон сохранен.")