import pytest
import allure
from models.contact import Contact
from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator
from selenium.common.exceptions import TimeoutException
from data.test_data import load_contact_data_from_csv


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================
@allure.severity(allure.severity_level.CRITICAL)
def test_add_contact_success_all_fields(authenticated_driver):
    # 1. Инициализируем страницу
    contact_page = ContactPage(authenticated_driver)

    # 2. Открываем форму добавления контакта
    contact_page.open()

    # 3. Генерируем уникальные тестовые данные через Faker
    contact = ContactGenerator.get_random_contact()

    # 4. Заполняем форму и сохраняем
    contact_page.fill_contact_form(contact)
    contact_page.submit_contact()

    # 5. ПРОВЕРКА: убеждаемся, что карточка с нужным телефоном появилась в списке.
    # Если метод is_contact_card_visible вернет False, тест упадет с понятным текстом.
    assert contact_page.is_contact_card_visible(contact.phone), \
        f"Ошибка: Карточка контакта с телефоном {contact.phone} не появилась в списке!"


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ (Данные берутся из CSV)
# ==========================================

@allure.severity(allure.severity_level.NORMAL)
# Вместо жестко прописанного списка мы просто вызываем функцию! (CSV)
@pytest.mark.parametrize("name, last_name, phone, email, address, description, expected_error", load_contact_data_from_csv())
def test_add_contact_negative(authenticated_driver, name, last_name, phone, email, address, description, expected_error):
    contact_page = ContactPage(authenticated_driver)
    contact_page.open()

    invalid_contact = Contact(
        name=name,
        last_name=last_name,
        phone=phone,
        email=email,
        address=address,
        description=description
    )

    contact_page.fill_contact_form(invalid_contact)
    contact_page.submit_contact()

    try:
        alert_text = contact_page.get_alert_text()
        assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"
        contact_page.accept_alert()
    except TimeoutException:
        pytest.fail(f"БАГ ПРИЛОЖЕНИЯ: Ожидаемый Alert с текстом '{expected_error}' так и не появился!")

    assert contact_page.is_add_tab_active(), "Вкладка ADD должна оставаться активной после попытки сдный контакт!"


@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG: Система позволяет создавать дубликаты по номеру телефона без Alert")
def test_add_contact_duplicate_phone(authenticated_driver):

    contact_page = ContactPage(authenticated_driver)

    # --- ШАГ 1: Создаем первый уникальный контакт ---
    contact_page.open()
    first_contact = ContactGenerator.get_random_contact()
    contact_page.fill_contact_form(first_contact)
    contact_page.submit_contact()

    # --- ШАГ 2: Пытаемся создать второй контакт с ТЕМ ЖЕ номером ---
    contact_page.open()
    duplicate_contact = ContactGenerator.get_random_contact()
    duplicate_contact.phone = first_contact.phone  # Копируем телефон из первого контакта!

    contact_page.fill_contact_form(duplicate_contact)
    contact_page.submit_contact()

    # --- ШАГ 3: Проверяем реакцию системы ---
    try:
        alert_text = contact_page.get_alert_text()
        print(f"\n[РАЗВЕДКА] УРА! Система выдала Alert: '{alert_text}'")
        contact_page.accept_alert()
        # Пока ставим заглушку, чтобы тест прошел, если алерт есть
        assert True
    except TimeoutException:
        pytest.fail("БАГ ПРИЛОЖЕНИЯ: Alert о дубликате телефона так и не появился! Контакт-клон сохранен.")