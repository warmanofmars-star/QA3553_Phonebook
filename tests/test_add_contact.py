import pytest
from models.contact import Contact
from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator
from selenium.common.exceptions import TimeoutException


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
@pytest.mark.parametrize("name, last_name, phone, email, address, description, expected_error", [

    # --- БЛОК 1: ПУСТЫЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ---
    ("", "Ivanov", "0501234567", "test@mail.com", "Tel Aviv", "desc", "Name cannot be empty!"),
    ("Ivan", "", "0501234567", "test@mail.com", "Tel Aviv", "desc", "Last Name cannot be empty!"),
    ("Ivan", "Ivanov", "", "test@mail.com", "Tel Aviv", "desc",
     "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
    # ИСПРАВЛЕНИЕ: Для пустого email тоже подставим русский текст, так как браузер реагирует на пустоту так же
    ("Ivan", "Ivanov", "0501234567", "", "Tel Aviv", "desc",
     "Email not valid: должно иметь формат адреса электронной почты"),
    ("Ivan", "Ivanov", "0501234567", "test@mail.com", "", "desc", "Address cannot be empty!"),

    # --- БЛОК 2: НЕВЕРНЫЙ ФОРМАТ ДАННЫХ ---
    # ИСПРАВЛЕНИЕ: Меняем ожидаемый текст на тот, который отдает русскоязычный браузер
    ("Ivan", "Ivanov", "0501234567", "not-an-email", "Tel Aviv", "desc",
     "Email not valid: должно иметь формат адреса электронной почты"),
    ("Ivan", "Ivanov", "abcdefghij", "test@mail.com", "Tel Aviv", "desc",
     "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
    ("Ivan", "Ivanov", "050123", "test@mail.com", "Tel Aviv", "desc",
     "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
])
def test_add_contact_negative(authenticated_driver, name, last_name, phone, email, address, description,
                              expected_error):
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

    # --- ИСПРАВЛЕНИЕ: Изящный перехват таймаута ---
    try:
        alert_text = contact_page.get_alert_text()
        assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"
        contact_page.accept_alert()
    except TimeoutException:
        # Если алерт не появился за 5 секунд, мы принудительно валим тест с понятным сообщением
        pytest.fail(f"БАГ ПРИЛОЖЕНИЯ: Ожидаемый Alert с текстом '{expected_error}' так и не появился!")

    # Проверка, что вкладка ADD осталась активной
    assert contact_page.is_add_tab_active(), "Вкладка ADD должна оставаться активной после попытки сохранить невалидный контакт!"