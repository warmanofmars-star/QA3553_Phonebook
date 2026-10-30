import allure
import pytest

from pages.contacts_page import ContactsPage
from utils.preconditions import require
from utils.waits import eventually

# Гибридные тесты: контакты создаются через API, удаляются через UI,
# результат проверяется и в UI (карточка исчезла), и через API (данные удалены)
pytestmark = [pytest.mark.ui, pytest.mark.hybrid, allure.epic("UI Testing"), allure.feature("Delete Contact")]


@pytest.mark.smoke
@allure.story("Delete one contact")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("TC-0036")
def test_delete_contact(authenticated_driver, auth_api, created_contact):
    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.delete_contact(created_contact.phone)

    assert contacts_page.is_card_gone(created_contact.phone), \
        f"Карточка с телефоном {created_contact.phone} не исчезла из списка"
    assert eventually(lambda: created_contact.id not in auth_api.get_contact_ids()), \
        "Карточка пропала из UI, но контакт остался на бэкенде"


@pytest.mark.regression
@allure.story("Delete several contacts")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_multiple_contacts(authenticated_driver, auth_api, create_contact):
    """Последовательное удаление нескольких конкретных контактов."""
    contacts = [create_contact() for _ in range(2)]

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    for contact in contacts:
        require(contacts_page.is_card_displayed(contact.phone), f"Предусловие: нет карточки {contact.phone}")

    for contact in contacts:
        contacts_page.delete_contact(contact.phone)
        assert contacts_page.is_card_gone(contact.phone), f"Карточка {contact.phone} не исчезла из списка"

    deleted_ids = {contact.id for contact in contacts}
    assert eventually(lambda: not deleted_ids & set(auth_api.get_contact_ids())), \
        "Карточки пропали из UI, но контакты остались на бэкенде"


@pytest.mark.regression
@allure.story("Delete all contacts one by one")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_all_contacts(authenticated_driver, auth_api, create_contact):
    """Удаление всех контактов пользователя через UI, по одному.

    Контакты создаются заранее: на пустом списке тест проходил бы всегда.
    """
    phones = [create_contact().phone for _ in range(3)]

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    # Ждём отрисовки карточек: иначе удаление увидело бы пустой (ещё не загруженный) список
    for phone in phones:
        require(contacts_page.is_card_displayed(phone), f"Предусловие: нет карточки {phone}")

    contacts_page.delete_all_contacts()

    assert contacts_page.cards_count() == 0, f"В списке осталось карточек: {contacts_page.cards_count()}"
    assert eventually(lambda: auth_api.get_contact_ids() == []), \
        "Карточки пропали из UI, но контакты остались на бэкенде"
