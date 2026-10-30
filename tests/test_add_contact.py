import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from data.test_data import load_negative_contacts
from pages.add_contact_page import AddContactPage
from pages.contacts_page import ContactsPage
from utils.waits import eventually

pytestmark = [pytest.mark.ui, allure.epic("UI Testing"), allure.feature("Add Contact")]


@pytest.mark.smoke
@allure.story("Add contact with all fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("TC-0011")
def test_add_contact_success_all_fields(authenticated_driver, auth_api):
    """Контакт, созданный через форму, появляется в списке и сохраняется со всеми полями."""
    contact = ContactGenerator.get_random_contact()

    add_page = AddContactPage(authenticated_driver)
    add_page.open()
    add_page.add_contact(contact)

    assert ContactsPage(authenticated_driver).is_card_displayed(contact.phone), \
        f"Карточка контакта с телефоном {contact.phone} не появилась в списке"

    # UI показывает только имя и телефон. Через API проверяем, что ВСЕ поля
    # сохранились, причём каждое в своё поле (не "съехали" в соседние инпуты)
    with allure.step("Проверить через API, что все поля сохранены верно"):
        stored = next((c for c in auth_api.get_contacts_list() if c.get("phone") == contact.phone), {})
        expected = contact.to_api_payload()
        actual = {key: stored.get(key) for key in expected}
        assert actual == expected, f"Сохранённые данные отличаются от введённых:\n{actual}\n!=\n{expected}"


@pytest.mark.regression
@allure.story("Negative Add Contact")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("contact, expected_error, test_case", load_negative_contacts())
def test_add_contact_negative(authenticated_driver, contact, expected_error, test_case):
    """Невалидные данные формы: должен появиться Alert с текстом из SRS (F5–F9),
    а пользователь остаться на вкладке ADD."""
    allure.dynamic.tag(test_case)  # связь с кейсом из STD

    add_page = AddContactPage(authenticated_driver)
    add_page.open()
    add_page.add_contact(contact)

    alert_text = add_page.wait_for_alert_text()
    assert alert_text is not None, f"Alert с ошибкой не появился (ожидался текст '{expected_error}')"
    assert expected_error in alert_text, f"Ожидалась ошибка '{expected_error}', но получено: '{alert_text}'"
    add_page.accept_alert()

    assert add_page.is_add_tab_active(), "После ошибки валидации пользователь должен остаться на вкладке ADD"


@pytest.mark.regression
@pytest.mark.hybrid
@allure.story("Add contact with duplicate phone")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0019")
@known_bug("DUPLICATE_CONTACT")
def test_add_contact_duplicate_phone(authenticated_driver, auth_api, create_contact):
    """SRS T45: телефон не должен повторять телефон ранее созданного контакта.

    Первый контакт создаётся через API (быстро и надёжно), дубликат — через UI.
    Результат проверяется через API: это источник правды о том, что сохранилось.
    """
    original = create_contact()

    add_page = AddContactPage(authenticated_driver)
    add_page.open()
    add_page.add_contact(ContactGenerator.get_random_contact(phone=original.phone))

    # Сохранение асинхронное: даём приложению время "сделать плохое"
    # и проверяем, что оно этого не сделало (см. utils/waits.py)
    duplicate_saved = eventually(
        lambda: sum(c.get("phone") == original.phone for c in auth_api.get_contacts_list()) > 1,
        timeout=5,
    )
    assert not duplicate_saved, f"Сохранён второй контакт с телефоном {original.phone}"
