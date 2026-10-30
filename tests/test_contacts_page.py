import pytest
import allure
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


# ==========================================
# ТЕСТ 1: Отображение созданного контакта
# ==========================================

@pytest.mark.smoke
@pytest.mark.ui
@allure.severity(allure.severity_level.CRITICAL)
def test_contact_is_visible_in_list(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_contact_is_visible_in_list ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    logger.info("ПОДГОТОВКА: Генерируем уникальные данные контакта")
    contact = ContactGenerator.get_random_contact()

    logger.info("ШАГ 1: Открываем страницу добавления контакта")
    add_page.open()

    logger.info(f"ШАГ 2: Заполняем форму и сохраняем контакт: {contact.name} {contact.last_name}")
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # МЫ БОЛЬШЕ НЕ КЛИКАЕМ НА ВКЛАДКУ CONTACTS
    # Приложение само делает редирект. Просто ждем появления карточки.
    logger.info(f"ПРОВЕРКА: Ожидаем авто-редирект и появление карточки с телефоном {contact.phone}")
    assert contacts_page.contact_card_visible(contact.phone), \
        f"Ошибка: Контакт с телефоном {contact.phone} не найден в списке!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# ТЕСТ 2: Открытие деталей контакта (Правая панель)
# ==========================================

@pytest.mark.smoke
@pytest.mark.ui
@allure.severity(allure.severity_level.CRITICAL)
def test_open_contact_details(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_open_contact_details ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    logger.info("ПОДГОТОВКА: Генерируем уникальные данные контакта")
    contact = ContactGenerator.get_random_contact()

    logger.info("ШАГ 1: Открываем страницу добавления и сохраняем новый контакт")
    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # Ждем авто-редирект
    logger.info("ШАГ 2: Ждем авто-редирект в список контактов")
    contacts_page.contact_card_visible(contact.phone)

    # Кликаем по созданной карточке
    logger.info(f"ШАГ 3: Кликаем по созданной карточке с телефоном: {contact.phone}")
    contacts_page.open_contact_details(contact.phone)

    # Читаем текст из появившейся правой панели
    logger.info("ШАГ 4: Читаем текст из появившейся правой панели деталей контакта")
    details_text = contacts_page.get_contact_details_text()

    # Проверка: Убеждаемся, что имя, фамилия и почта есть в этом тексте
    logger.info("ПРОВЕРКА: Убеждаемся, что Имя, Фамилия и Email корректно отображаются в деталях")
    assert contact.name in details_text, f"Имя '{contact.name}' не найдено в деталях карточки!"
    assert contact.last_name in details_text, f"Фамилия '{contact.last_name}' не найдена в деталях!"
    assert contact.email in details_text, f"Email '{contact.email}' не найден в деталях!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")