import pytest
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator


# ==========================================
# ТЕСТ 1: Отображение созданного контакта
# ==========================================
def test_contact_is_visible_in_list(authenticated_driver):
    add_page = ContactPage(authenticated_driver)
    contact = ContactGenerator.get_random_contact()

    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # МЫ БОЛЬШЕ НЕ КЛИКАЕМ НА ВКЛАДКУ CONTACTS
    # Приложение само делает редирект. Просто ждем появления карточки.
    contacts_page = ContactsPage(authenticated_driver)
    assert contacts_page.contact_card_visible(contact.phone), \
        f"Ошибка: Контакт с телефоном {contact.phone} не найден в списке!"


# ==========================================
# ТЕСТ 2: Подтверждение бага с дубликатами
# ==========================================
@pytest.mark.xfail(reason="BUG: Система позволяет создавать дубликаты, и они ОБА появляются в списке")
def test_duplicate_contact_cards_count(authenticated_driver):
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    contact = ContactGenerator.get_random_contact()

    # Создаем ПЕРВЫЙ контакт
    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # Обязательно ждем окончания авто-редиректа, чтобы данные точно ушли в базу
    contacts_page.contact_card_visible(contact.phone)

    # Создаем ВТОРОЙ контакт с ТЕМИ ЖЕ данными
    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    # Снова ждем авто-редирект
    contacts_page.contact_card_visible(contact.phone)

    # Теперь считаем карточки. Если баг на месте, их будет 2!
    count = contacts_page.contact_cards_count(contact.phone)
    assert count == 1, f"Ожидалась 1 карточка, но найдено {count}. Интерфейс отрисовал дубликат!"


# ==========================================
# ТЕСТ 3: Открытие деталей контакта (Правая панель)
# ==========================================
def test_open_contact_details(authenticated_driver):
    add_page = ContactPage(authenticated_driver)
    contact = ContactGenerator.get_random_contact()

    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()

    contacts_page = ContactsPage(authenticated_driver)
    # Ждем авто-редирект
    contacts_page.contact_card_visible(contact.phone)

    # Кликаем по созданной карточке
    contacts_page.open_contact_details(contact.phone)

    # Читаем текст из появившейся правой панели
    details_text = contacts_page.get_contact_details_text()

    # Проверка: Убеждаемся, что имя, фамилия и почта есть в этом тексте
    assert contact.name in details_text, f"Имя '{contact.name}' не найдено в деталях карточки!"
    assert contact.last_name in details_text, f"Фамилия '{contact.last_name}' не найдена в деталях!"
    assert contact.email in details_text, f"Email '{contact.email}' не найден в деталях!"