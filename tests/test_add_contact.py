import pytest
import allure
from pages.add_contact_page import ContactPage
from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from data.test_data import load_negative_contacts
from utils.logger import get_logger
from utils.waits import eventually

# Создаем логгер для тестов
logger = get_logger("TEST")


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================

@pytest.mark.smoke
@pytest.mark.ui
@allure.epic("UI Testing")
@allure.feature("Contacts Management")
@allure.story("Test Add Contact Success All Fields")
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

@pytest.mark.regression
@pytest.mark.ui
@allure.epic("UI Testing")
@allure.feature("Contacts Management")
@allure.story("Negative Add Contact")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("contact, expected_error, test_case", load_negative_contacts())
def test_add_contact_negative(authenticated_driver, contact, expected_error, test_case):
    """Невалидные данные формы: должен появиться Alert с текстом из SRS (F5–F9),
    а пользователь остаться на вкладке ADD."""
    allure.dynamic.tag(test_case)  # связь с кейсом из STD
    contact_page = ContactPage(authenticated_driver)

    logger.info("ШАГ 1: Открываем страницу добавления контакта")
    contact_page.open()

    logger.info("ШАГ 2: Заполняем форму невалидными данными и нажимаем Save")
    contact_page.fill_contact_form(contact)
    contact_page.submit_contact()

    logger.info(f"ПРОВЕРКА 1: Ожидаем Alert с текстом: '{expected_error}'")
    alert_text = contact_page.wait_for_alert_text()
    assert alert_text is not None, f"Alert с ошибкой не появился (ожидался текст '{expected_error}')"
    assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"
    contact_page.accept_alert()

    logger.info("ПРОВЕРКА 2: Вкладка ADD должна оставаться активной")
    assert contact_page.is_add_tab_active(), \
        "Вкладка ADD должна оставаться активной после попытки сохранить невалидный контакт!"


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.hybrid
@allure.epic("UI Testing")
@allure.feature("Contacts Management")
@allure.story("Test Add contact: Duplicate Phone")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0019")
@known_bug("DUPLICATE_CONTACT")
def test_add_contact_duplicate_phone(authenticated_driver, auth_api, create_contact):
    """SRS T45: телефон не должен повторять телефон ранее созданного контакта.

    Первый контакт создаётся через API (быстро и надёжно), дубликат — через UI.
    Результат проверяется через API: это источник правды о том, что сохранилось.
    """
    original = create_contact()
    contact_page = ContactPage(authenticated_driver)

    logger.info(f"ШАГ 1: Пытаемся через UI создать контакт с тем же телефоном {original.phone}")
    contact_page.open()
    contact_page.fill_contact_form(ContactGenerator.get_random_contact(phone=original.phone))
    contact_page.submit_contact()

    logger.info("ПРОВЕРКА: дубликат не должен сохраниться")
    # Сохранение асинхронное: даём приложению время "сделать плохое"
    # и проверяем, что оно этого не сделало. Проверка сразу после клика
    # могла бы пройти при живом баге — запрос ещё не дошёл бы до бэкенда.
    duplicate_saved = eventually(
        lambda: sum(c.get("phone") == original.phone for c in auth_api.get_contacts_list()) > 1,
        timeout=5,
    )
    assert not duplicate_saved, f"Сохранён второй контакт с телефоном {original.phone}"
