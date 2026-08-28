import pytest
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from models.contact import Contact


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ (TC-021 - TC-027)
# ==========================================
def test_edit_contact_positive(authenticated_driver):
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем исходный контакт
    old_contact = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(old_contact)
    add_page.submit_contact()
    contacts_page.contact_card_visible(old_contact.phone)  # Ждем авто-редирект

    # 2. Подготовка: Генерируем новые данные для замены
    new_contact = ContactGenerator.get_random_contact()

    # 3. ШАГИ ТЕСТА
    contacts_page.open_contact_details(old_contact.phone)  # Открываем старую карточку
    contacts_page.click_edit_button()  # Жмем Edit
    contacts_page.edit_contact_form(new_contact)  # Вводим новые данные
    contacts_page.click_save_edit_button()  # Сохраняем

    # 4. ПРОВЕРКА
    # Ждем, пока старая карточка пропадет и появится новая (по новому телефону)
    assert contacts_page.contact_card_visible(new_contact.phone), "Измененный контакт не появился в списке слева!"

    # Открываем измененную карточку и проверяем текст справа
    contacts_page.open_contact_details(new_contact.phone)
    details_text = contacts_page.get_contact_details_text()

    assert new_contact.name in details_text, "Новое имя не сохранилось!"
    assert new_contact.last_name in details_text, "Новая фамилия не сохранилась!"


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ (TC-035)
# ==========================================
@pytest.mark.xfail(reason="BUG: Система позволяет редактировать телефон на уже существующий дубликат")
def test_edit_contact_duplicate_phone(authenticated_driver):
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем ДВА разных контакта
    contact_1 = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact_1)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact_1.phone)

    contact_2 = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact_2)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact_2.phone)

    # 2. ШАГИ ТЕСТА: Редактируем Контакт 2, подсовывая ему телефон от Контакта 1
    contacts_page.open_contact_details(contact_2.phone)
    contacts_page.click_edit_button()

    # Вот тут срабатывает магия **overrides, мы переопределяем только телефон!
    duplicate_data = ContactGenerator.get_random_contact(phone=contact_1.phone)
    contacts_page.edit_contact_form(duplicate_data)
    contacts_page.click_save_edit_button()

    # 3. ПРОВЕРКА
    # По требованиям (T83, F13) система не должна сохранять такой контакт.
    # Значит, форма редактирования должна остаться открытой (или должна быть ошибка).
    assert contacts_page.is_edit_form_open(), "Баг: Система сохранила дубликат при редактировании и закрыла форму!"


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ: Очистка обязательных полей (TC-028 - TC-033)
# ==========================================
@pytest.mark.xfail(reason="BUG: Фронтенд позволяет сохранять контакт с пустыми обязательными полями при редактировании")
@pytest.mark.parametrize("field_to_clear", ["name", "last_name", "phone", "email", "address"])
def test_edit_contact_clear_required_fields(authenticated_driver, field_to_clear):
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем валидный контакт
    contact = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(contact)
    add_page.submit_contact()
    contacts_page.contact_card_visible(contact.phone)  # Ждем авто-редирект

    # 2. Открываем созданную карточку и жмем Edit
    contacts_page.open_contact_details(contact.phone)
    contacts_page.click_edit_button()

    # 3. ШАГ ТЕСТА: Очищаем ТОЛЬКО ОДНО обязательное поле
    # Создаем объект Contact, где все поля None (наш метод edit_contact_form их пропустит)
    empty_update = Contact(name=None, last_name=None, phone=None, email=None, address=None, description=None)

    # Динамически устанавливаем нужному полю значение пустой строки ""
    setattr(empty_update, field_to_clear, "")

    # Передаем это в форму. Метод сотрет только то поле, которое мы передали как ""
    contacts_page.edit_contact_form(empty_update)
    contacts_page.click_save_edit_button()

    # 4. ПРОВЕРКА: Кнопка Save не должна сработать, форма должна остаться открытой
    assert contacts_page.is_edit_form_open(), f"БАГ (F10-F14): Система сохранила контакт с пустым полем '{field_to_clear}'!"