import os
import allure
import pytest
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


@allure.severity(allure.severity_level.CRITICAL)
def test_delete_contact(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_delete_contact ---")

    # ==========================================
    # ПРЕДУСЛОВИЕ: Создаем контакт для удаления
    # ==========================================
    logger.info("ПОДГОТОВКА: Открываем форму и генерируем контакт для удаления")
    add_page = ContactPage(authenticated_driver)
    add_page.open()

    # Генерируем тестовые данные
    contact = ContactGenerator.get_random_contact()

    # Сохраняем контакт
    logger.info(f"ПОДГОТОВКА: Сохраняем контакт с телефоном: {contact.phone}")
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # Убеждаемся, что контакт успешно создался (иначе нет смысла проверять удаление)
    logger.info("ПОДГОТОВКА: Убеждаемся, что контакт успешно появился в списке")
    assert add_page.is_contact_card_visible(contact.phone), "Предусловие сломалось: контакт не создался!"

    # ==========================================
    # ШАГ ТЕСТА: Удаляем созданный контакт
    # ==========================================
    contacts_page = ContactsPage(authenticated_driver)

    # 1. Открываем страницу контактов (хотя мы уже на ней, это хорошая практика)
    logger.info("ШАГ 1: Открываем страницу со списком контактов")
    contacts_page.open()

    # 2. Кликаем по карточке с нашим уникальным телефоном
    logger.info(f"ШАГ 2: Кликаем по карточке контакта ({contact.phone}) для открытия деталей")
    contacts_page.open_contact_details(contact.phone)

    # 3. Нажимаем кнопку Remove
    logger.info("ШАГ 3: Нажимаем кнопку Remove (Удалить)")
    contacts_page.click_remove_button()

    # ==========================================
    # ПРОВЕРКА: Контакт исчез
    # ==========================================
    logger.info(f"ПРОВЕРКА: Убеждаемся, что карточка с телефоном {contact.phone} полностью исчезла из списка")
    assert contacts_page.is_contact_deleted(contact.phone), \
        f"Ошибка: Карточка с телефоном {contact.phone} не удалилась из списка!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# здесь у нас будет метод удаления всех контактов (пылесос с тумблером)
# Читаем наш рубильник из .env
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'


@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_delete_all_contacts(authenticated_driver):
    """Скрипт-утилита: Полное очищение списка контактов"""
    logger.info("--- ЗАПУСК ТЕСТА-УТИЛИТЫ: test_delete_all_contacts ---")
    logger.warning("ВНИМАНИЕ: Активирован 'пылесос' — начато массовое удаление всех контактов из базы!")
    contacts_page = ContactsPage(authenticated_driver)

    # ==========================================
    # ШАГ ТЕСТА: Запускаем "пылесос"
    # ==========================================
    logger.info("ШАГ 1: Запускаем цикл удаления...")
    contacts_page.delete_all_contacts()

    # ==========================================
    # ПРОВЕРКА: Список должен быть абсолютно пуст
    # ==========================================
    final_count = contacts_page.get_all_contacts_count()
    logger.info(f"ПРОВЕРКА: Проверяем, что список абсолютно пуст. Найдено контактов: {final_count}")

    assert final_count == 0, f"Ошибка: Ожидалось 0 контактов, но осталось {final_count}!"
    logger.info("--- ТЕСТ-УТИЛИТА УСПЕШНО ЗАВЕРШЕНА ---")


# здесь у нас метод удаления всех созданных временных контактов для проверки метода
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_multiple_contacts(authenticated_driver):
    """Проверка последовательного удаления нескольких конкретных контактов"""
    logger.info("--- ЗАПУСК ТЕСТА: test_delete_multiple_contacts ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    phones_to_delete = []

    # Создаем 2 контакта и запоминаем их номера
    logger.info("ПОДГОТОВКА: Запускаем цикл создания 2 временных контактов")
    for i in range(2):
        add_page.open()
        contact = ContactGenerator.get_random_contact()
        add_page.fill_contact_form(contact)
        add_page.submit_contact()
        contacts_page.contact_card_visible(contact.phone)
        phones_to_delete.append(contact.phone)
        logger.info(f"  -> Создан временный контакт №{i + 1} с телефоном: {contact.phone}")

    # Запоминаем общее количество контактов ДО удаления
    initial_count = contacts_page.get_all_contacts_count()
    logger.info(f"ПОДГОТОВКА: Запоминаем общее количество контактов ДО удаления: {initial_count}")

    # Точечно удаляем только созданные контакты
    logger.info(f"ШАГ 1: Запускаем точечное удаление по собранному списку: {phones_to_delete}")
    contacts_page.delete_specific_contacts(phones_to_delete)

    # Общее количество должно уменьшиться ровно на 2
    final_count = contacts_page.get_all_contacts_count()
    logger.info(f"ПРОВЕРКА: Общее количество должно уменьшиться ровно на 2. Текущее количество: {final_count}")

    assert final_count == initial_count - 2, \
        f"Ошибка: Ожидалось {initial_count - 2} контактов, но осталось {final_count}!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")