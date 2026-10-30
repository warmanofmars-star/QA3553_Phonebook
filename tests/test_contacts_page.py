import allure
import pytest

from pages.contacts_page import ContactsPage

pytestmark = [pytest.mark.ui, pytest.mark.hybrid, allure.epic("UI Testing"), allure.feature("Contacts List")]


@pytest.mark.smoke
@allure.story("Contact is shown in the list")
@allure.severity(allure.severity_level.CRITICAL)
def test_contact_is_visible_in_list(authenticated_driver, created_contact):
    """Контакт, созданный на бэкенде, отображается в списке.

    Раньше контакт создавался через форму, и тест дублировал test_add_contact_success_all_fields.
    Теперь он проверяет отдельную вещь — отрисовку данных бэкенда в списке.
    """
    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()

    assert contacts_page.is_card_displayed(created_contact.phone), \
        f"Контакт с телефоном {created_contact.phone} не найден в списке"


@pytest.mark.smoke
@allure.story("Contact details panel")
@allure.severity(allure.severity_level.CRITICAL)
def test_open_contact_details(authenticated_driver, created_contact):
    """Панель деталей показывает все данные контакта."""
    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.open_details(created_contact.phone)

    details = contacts_page.details_text()
    with allure.step("Проверить, что все поля контакта есть в панели деталей"):
        for field in ("name", "last_name", "phone", "email", "address", "description"):
            value = getattr(created_contact, field)
            assert value in details, f"Поле {field}='{value}' не найдено в деталях контакта:\n{details}"
