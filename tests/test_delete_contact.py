from models.contact import Contact
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactListPage
from data.data_generator import ContactGenerator


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
    contacts_page = ContactListPage(authenticated_driver)

    # 1. Открываем страницу контактов (хотя мы уже на ней, это хорошая практика)
    contacts_page.open()

    # 2. Кликаем по карточке с нашим уникальным телефоном
    contacts_page.click_contact_by_phone(contact.phone)

    # 3. Нажимаем кнопку Remove
    contacts_page.click_remove_button()

    # ==========================================
    # ПРОВЕРКА: Контакт исчез
    # ==========================================
    assert contacts_page.is_contact_deleted(contact.phone), \
        f"Ошибка: Карточка с телефоном {contact.phone} не удалилась из списка!"