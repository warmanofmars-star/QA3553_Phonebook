import pytest
import allure
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from models.contact import Contact
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================
@allure.severity(allure.severity_level.CRITICAL)
def test_edit_contact_positive(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_edit_contact_positive ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем исходный контакт
    logger.info("ПОДГОТОВКА: Создаем исходный (старый) контакт")
    old_contact = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(old_contact)
    add_page.submit_contact()
    contacts_page.contact_card_visible(old_contact.phone)  # Ждем авто-редирект

    # 2. Подготовка: Генерируем новые данные для замены
    logger.info("ПОДГОТОВКА: Генерируем новые данные для замены")
    new_contact = ContactGenerator.get_random_contact()

    # 3. ШАГИ ТЕСТА
    logger.info(f"ШАГ 1: Открываем карточку старого контакта (тел: {old_contact.phone}) и жмем Edit")
    contacts_page.open_contact_details(old_contact.phone)  # Открываем старую карточку
    contacts_page.click_edit_button()  # Жмем Edit

    logger.info(f"ШАГ 2: Вводим новые данные (имя: {new_contact.name}) и сохраняем")
    contacts_page.edit_contact_form(new_contact)  # Вводим новые данные
    contacts_page.click_save_edit_button()  # Сохраняем

    # 4. ПРОВЕРКА
    logger.info("ПРОВЕРКА 1: Убеждаемся, что измененный контакт появился в списке слева")
    assert contacts_page.contact_card_visible(new_contact.phone), "Измененный контакт не появился в списке слева!"

    # Снова открываем детали и жмем Edit, чтобы увидеть форму с сохраненными данными
    logger.info("ШАГ 3: Снова открываем детали измененного контакта и жмем Edit для строгой проверки полей")
    contacts_page.open_contact_details(new_contact.phone)
    contacts_page.click_edit_button()

    # Забираем данные ТОЧНО из своих полей!
    logger.info("ШАГ 4: Считываем сохраненные значения прямо из инпутов формы (Senior подход)")
    saved_contact = contacts_page.get_contact_data_from_form()

    # Точечные жесткие проверки (Строгое равенство!)
    logger.info("ПРОВЕРКА 2: Строго сравниваем сохраненные данные с теми, что мы отправляли")
    assert saved_contact.name == new_contact.name, f"Баг маппинга! Имя съехало. Ожидали {new_contact.name}, получили {saved_contact.name}"
    assert saved_contact.last_name == new_contact.last_name, "Баг маппинга! Фамилия сохранилась не туда!"
    assert saved_contact.email == new_contact.email, "Баг маппинга! Email сохранился не туда!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ: Дубликаты (TC-034, TC-035)
# ==========================================
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG: Фронтенд позволяет редактировать телефон на уже существующий дубликат")
def test_edit_contact_duplicate_phone(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_edit_contact_duplicate_phone ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем ДВА разных контакта
    logger.info("ПОДГОТОВКА: Создаем Контакт №1")
    contact_1 = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact_1)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact_1.phone)

    logger.info("ПОДГОТОВКА: Создаем Контакт №2")
    contact_2 = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact_2)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact_2.phone)

    # 2. ШАГИ ТЕСТА: Редактируем Контакт 2, подсовывая ему телефон от Контакта 1
    logger.info(
        f"ШАГ 1: Открываем Контакт №2 и пытаемся изменить его телефон на телефон Контакта №1 ({contact_1.phone})")
    contacts_page.open_contact_details(contact_2.phone)
    contacts_page.click_edit_button()

    # Переопределяем только телефон через kwargs генератора
    duplicate_data = ContactGenerator.get_random_contact(phone=contact_1.phone)
    contacts_page.edit_contact_form(duplicate_data)
    contacts_page.click_save_edit_button()

    # 3. ПРОВЕРКА
    logger.info("ПРОВЕРКА: Форма редактирования должна остаться открытой (ошибка дубликата)")
    is_open = contacts_page.is_edit_form_open()

    if not is_open:
        logger.error("БАГ ПРИЛОЖЕНИЯ: Система сохранила дубликат при редактировании и закрыла форму!")

    assert is_open, "Баг: Система сохранила дубликат при редактировании и закрыла форму!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН (Баг починили?) ---")


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ: Очистка обязательных полей (TC-028 - TC-033)
# ==========================================
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG: Фронтенд позволяет сохранять контакт с пустыми обязательными полями при редактировании")
@pytest.mark.parametrize("field_to_clear", ["name", "last_name", "phone", "email", "address"])
def test_edit_contact_clear_required_fields(authenticated_driver, field_to_clear):
    logger.info(f"--- ЗАПУСК ТЕСТА: test_edit_contact_clear_required_fields (Поле для очистки: '{field_to_clear}') ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем валидный контакт
    logger.info("ПОДГОТОВКА: Создаем валидный контакт для последующего редактирования")
    contact = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact.phone)

    # 2. Открываем созданную карточку и жмем Edit
    logger.info("ШАГ 1: Открываем созданную карточку и переходим в режим редактирования")
    contacts_page.open_contact_details(contact.phone)
    contacts_page.click_edit_button()

    # 3. ШАГ ТЕСТА: Очищаем ТОЛЬКО ОДНО обязательное поле
    logger.info(f"ШАГ 2: Очищаем обязательное поле '{field_to_clear}' и нажимаем Save")
    empty_update = Contact(**{field_to_clear: ""})

    contacts_page.edit_contact_form(empty_update)
    contacts_page.click_save_edit_button()

    # 4. ПРОВЕРКА: Форма должна остаться открытой (система не должна принимать пустые значения)
    logger.info("ПРОВЕРКА: Форма редактирования должна остаться открытой (сохранение невалидного контакта запрещено)")
    is_open = contacts_page.is_edit_form_open()

    if not is_open:
        logger.error(f"БАГ ПРИЛОЖЕНИЯ: Система сохранила контакт с пустым полем '{field_to_clear}'!")

    assert is_open, f"БАГ: Система сохранила контакт с пустым полем '{field_to_clear}'!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН (Баг починили?) ---")