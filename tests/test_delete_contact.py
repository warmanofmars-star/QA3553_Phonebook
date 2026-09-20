import os
import allure
import pytest
from selenium.webdriver.support.wait import WebDriverWait
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from utils.api_helper import make_api_request
from utils.logger import get_logger

logger = get_logger("TEST")
API_URL = os.getenv("API_URL")


# ==========================================
# 1. ТЕСТ ОДИНОЧНОГО УДАЛЕНИЯ
# ==========================================
@allure.epic("Hybrid Testing")
@allure.feature("Contacts Management")
@allure.story("API Setup -> UI Delete -> UI Assert")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_contact(authenticated_driver, api_token):
    logger.info("--- ЗАПУСК ГИБРИДНОГО ТЕСТА: test_delete_contact ---")

    with allure.step("API PRECONDITION: Создаем контакт через бэкенд"):
        contact = ContactGenerator.get_random_contact()
        headers = {"Authorization": f"Bearer {api_token}"}

        response = make_api_request("POST", f"{API_URL}/v1/contacts", json=contact.to_api_payload(), headers=headers)
        assert response.status_code == 200, "Пререквизит упал: API не создал контакт"
        logger.info(f"API успешно создал контакт с телефоном: {contact.phone}")

    # Инициализируем страницу ДО ее использования
    contacts_page = ContactsPage(authenticated_driver)

    with allure.step("UI SCENARIO: Открываем карточку и удаляем контакт"):
        contacts_page.open()
        logger.info(f"ШАГ 1: Кликаем по карточке контакта ({contact.phone})")
        contacts_page.open_contact_details(contact.phone)
        logger.info("ШАГ 2: Нажимаем кнопку Remove")
        contacts_page.click_remove_button()

    with allure.step(f"UI ASSERT: Проверяем, что карточка исчезла"):
        assert contacts_page.is_contact_deleted(contact.phone), \
            f"Ошибка: Карточка с телефоном {contact.phone} не удалилась из списка!"
        logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# 2. МАССОВОЕ УДАЛЕНИЕ (Пылесос)
# ==========================================
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'


@allure.epic("UI Testing")
@allure.feature("Contacts Management")
@allure.story("Mass Delete Utilities")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_delete_all_contacts(authenticated_driver):
    """Скрипт-утилита: Полное очищение списка контактов через UI"""
    logger.info("--- ЗАПУСК ТЕСТА-УТИЛИТЫ: test_delete_all_contacts ---")
    contacts_page = ContactsPage(authenticated_driver)

    contacts_page.open()
    contacts_page.delete_all_contacts()

    final_count = contacts_page.get_all_contacts_count()
    assert final_count == 0, f"Ошибка: Ожидалось 0 контактов, но осталось {final_count}!"


# ==========================================
# 3. МНОЖЕСТВЕННОЕ ТОЧЕЧНОЕ УДАЛЕНИЕ
# ==========================================
@allure.epic("Hybrid Testing")
@allure.feature("Contacts Management")
@allure.story("API Setup -> UI Multiple Delete")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_multiple_contacts(authenticated_driver, api_token):
    """Проверка последовательного удаления нескольких конкретных контактов"""
    logger.info("--- ЗАПУСК ГИБРИДНОГО ТЕСТА: test_delete_multiple_contacts ---")
    contacts_page = ContactsPage(authenticated_driver)

    phones_to_delete = []

    with allure.step("API PRECONDITION: Создаем 2 временных контакта через бэкенд"):
        headers = {"Authorization": f"Bearer {api_token}"}

        for i in range(2):
            contact = ContactGenerator.get_random_contact()
            response = make_api_request("POST", f"{API_URL}/v1/contacts", json=contact.to_api_payload(),
                                        headers=headers)
            assert response.status_code == 200, f"Ошибка API: Не удалось создать контакт №{i + 1}"

            phones_to_delete.append(contact.phone)
            logger.info(f"  -> API создал временный контакт №{i + 1} с телефоном: {contact.phone}")

    with allure.step(f"UI SCENARIO: Точечное удаление контактов из списка: {phones_to_delete}"):
        contacts_page.open()

        logger.info("СИНХРОНИЗАЦИЯ: Ждем, пока React отрисует массив карточек в DOM")
        WebDriverWait(authenticated_driver, 10).until(
            lambda d: len(d.find_elements(*contacts_page.CONTACT_CARDS)) > 0,
            message="Список контактов так и не загрузился!"
        )

        contacts_page.contact_card_visible(phones_to_delete[0])

        initial_count = contacts_page.get_all_contacts_count()
        logger.info(f"ПОДГОТОВКА: Запоминаем количество контактов ДО удаления: {initial_count}")

        contacts_page.delete_specific_contacts(phones_to_delete)

    with allure.step("UI ASSERT: Проверяем, что общее количество уменьшилось ровно на 2"):
        final_count = contacts_page.get_all_contacts_count()
        logger.info(f"ПРОВЕРКА: Количество ПОСЛЕ удаления: {final_count}")

        assert final_count == initial_count - 2, \
            f"Ошибка: Ожидалось {initial_count - 2} контактов, но осталось {final_count}!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")