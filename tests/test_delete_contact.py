import os
import allure
import pytest
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator

@allure.severity(allure.severity_level.CRITICAL)
def test_delete_contact(authenticated_driver):
    # ==========================================
    # ПРЕДУСЛОВИЕ: Создаем контакт для удаления
    # ==========================================
    add_page = ContactPage(authenticated_driver)
    add_page.open()

    # Генерируем тестовые данные
    contact = ContactGenerator.get_random_contact()

    # Сохраняем контакт
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # Убеждаемся, что контакт успешно создался (иначе нет смысла проверять удаление)
    assert add_page.is_contact_card_visible(contact.phone), "Предусловие сломалось: контакт не создался!"

    # ==========================================
    # ШАГ ТЕСТА: Удаляем созданный контакт
    # ==========================================
    contacts_page = ContactsPage(authenticated_driver)

    # 1. Открываем страницу контактов (хотя мы уже на ней, это хорошая практика)
    contacts_page.open()

    # 2. Кликаем по карточке с нашим уникальным телефоном
    contacts_page.open_contact_details(contact.phone)

    # 3. Нажимаем кнопку Remove
    contacts_page.click_remove_button()

    # ==========================================
    # ПРОВЕРКА: Контакт исчез
    # ==========================================
    assert contacts_page.is_contact_deleted(contact.phone), \
        f"Ошибка: Карточка с телефоном {contact.phone} не удалилась из списка!"

#здесь у нас будет метод удаления всех контактов
# Читаем наш рубильник из .env
ALLOW_MASS_DELETE = os.getenv("ALLOW_MASS_DELETE") == 'true'

@allure.severity(allure.severity_level.CRITICAL)
# Если рубильник выключен, Pytest пропустит этот тест и напишет причину
@pytest.mark.skipif(not ALLOW_MASS_DELETE, reason="Предохранитель: Массовое удаление отключено в .env")
def test_delete_all_contacts(authenticated_driver):
    """Проверка полного очищения списка контактов"""
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # ==========================================
    # ПРЕДУСЛОВИЕ: Создаем 2 контакта (если список пуст)
    # ==========================================
    for _ in range(2):
        add_page.open()
        contact = ContactGenerator.get_random_contact()
        add_page.fill_contact_form(contact)
        add_page.submit_contact()

        # Обязательно ждем редирект и появление карточки, чтобы данные ушли в базу
        contacts_page.contact_card_visible(contact.phone)

    # ==========================================
    # ШАГИ ТЕСТА: Запускаем "пылесос"
    # ==========================================
    contacts_page.delete_all_contacts()

    # ==========================================
    # ПРОВЕРКА: Список должен быть абсолютно пуст
    # ==========================================
    final_count = contacts_page.get_all_contacts_count()
    assert final_count == 0, f"Ошибка: Ожидалось 0 контактов, но осталось {final_count}!"