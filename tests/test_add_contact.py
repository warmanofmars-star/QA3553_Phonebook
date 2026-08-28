import pytest
from models.contact import Contact
from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator
from selenium.common.exceptions import TimeoutException
from data.test_data import NEGATIVE_CONTACT_DATA


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================
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
# НЕГАТИВНЫЕ ТЕСТЫ (Проверка валидации полей из ТЗ)
# ==========================================

@pytest.mark.parametrize("name, last_name, phone, email, address, description, expected_error", NEGATIVE_CONTACT_DATA)
def test_add_contact_negative(authenticated_driver, name, last_name, phone, email, address, description, expected_error):
    contact_page = ContactPage(authenticated_driver)
    contact_page.open()

    invalid_contact = Contact(name, last_name, phone, email, address, description)

    contact_page.fill_contact_form(invalid_contact)
    contact_page.submit_contact()

    try:
        alert_text = contact_page.get_alert_text()
        assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"
        contact_page.accept_alert()
    except TimeoutException:
        pytest.fail(f"БАГ ПРИЛОЖЕНИЯ: Ожидаемый Alert с текстом '{expected_error}' так и не появился!")

    assert contact_page.is_add_tab_active(), "Вкладка ADD должна оставаться активной после попытки сохранить невалидный контакт!"