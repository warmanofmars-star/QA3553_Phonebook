from dataclasses import replace

import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from models.contact import Contact
from pages.contacts_page import ContactsPage
from utils.waits import eventually

# Все тесты файла гибридные: предусловия — через API (фикстуры), действие — через UI,
# результат — через API. Требования F10–F14 звучат как "система не сохраняет
# невалидные данные", поэтому проверяем именно сохранение, а не поведение формы.
pytestmark = [pytest.mark.ui, pytest.mark.hybrid, allure.epic("UI Testing"), allure.feature("Edit Contact")]


def _stored_contact(api, contact_id) -> dict:
    """Контакт в том виде, в каком он сохранён на бэкенде."""
    return next((c for c in api.get_contacts_list() if c.get("id") == contact_id), {})


def _saved_fields(api, contact: Contact) -> dict:
    """Сохранённые на бэкенде значения тех полей, которые есть в payload контакта."""
    stored = _stored_contact(api, contact.id)
    return {key: stored.get(key) for key in contact.to_api_payload()}


# Как в STD: каждое поле меняется отдельным кейсом (TC-00021 ... TC-00026).
# Это не формальность: если бы все поля проверялись одним тестом, известный баг
# в описании сделал бы xfail весь тест — и спрятал бы поломку любого другого поля.
EDIT_FIELD_CASES = [
    pytest.param("name", "TC-0021", id="name"),
    pytest.param("last_name", "TC-0022", id="last_name"),
    pytest.param("email", "TC-0023", id="email"),
    pytest.param("phone", "TC-0024", id="phone"),
    pytest.param("address", "TC-0025", id="address"),
    pytest.param("description", "TC-0026", id="description", marks=known_bug("EDIT_DESCRIPTION_BROKEN")),
]


@pytest.mark.smoke
@allure.story("Edit one field")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("field, test_case", EDIT_FIELD_CASES)
def test_edit_contact_single_field(authenticated_driver, auth_api, created_contact, field, test_case):
    """Изменение одного поля сохраняется, а остальные поля остаются прежними."""
    allure.dynamic.tag(test_case)
    new_value = getattr(ContactGenerator.get_random_contact(), field)
    expected = replace(created_contact, **{field: new_value})

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact.phone, Contact(**{field: new_value}))

    with allure.step("Проверить через API, что изменилось только нужное поле"):
        before = created_contact.to_api_payload()
        changed = eventually(lambda: _saved_fields(auth_api, created_contact) != before, timeout=5)
        assert changed, "Изменения не сохранились на бэкенде"
        actual = _saved_fields(auth_api, created_contact)
        assert actual == expected.to_api_payload(), \
            f"Сохранённые данные отличаются от ожидаемых:\n{actual}\n!=\n{expected.to_api_payload()}"


@pytest.mark.regression
@allure.story("Edit all fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("TC-0027")
@known_bug("EDIT_DESCRIPTION_BROKEN")
def test_edit_contact_all_fields(authenticated_driver, auth_api, created_contact):
    """Все поля контакта меняются за одно редактирование, каждое сохраняется в своё поле."""
    expected = replace(ContactGenerator.get_random_contact(), id=created_contact.id)

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact.phone, expected)

    assert contacts_page.is_card_displayed(expected.phone), "Изменённый контакт не появился в списке"

    with allure.step("Проверить через API, что все поля сохранены верно"):
        updated = eventually(
            lambda: _stored_contact(auth_api, created_contact.id).get("phone") == expected.phone,
            timeout=5,
        )
        assert updated, "Изменения не сохранились на бэкенде"
        actual = _saved_fields(auth_api, created_contact)
        assert actual == expected.to_api_payload(), \
            f"Сохранённые данные отличаются от введённых:\n{actual}\n!=\n{expected.to_api_payload()}"


@pytest.mark.regression
@allure.story("Edit with duplicate phone")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0035")
@known_bug("DUPLICATE_CONTACT")
def test_edit_contact_duplicate_phone(authenticated_driver, auth_api, create_contact):
    """SRS T83: при редактировании телефон не должен повторять телефон другого контакта."""
    contact_1 = create_contact()
    contact_2 = create_contact()

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(contact_2.phone, Contact(phone=contact_1.phone))  # меняем только телефон

    duplicate_saved = eventually(
        lambda: _stored_contact(auth_api, contact_2.id).get("phone") == contact_1.phone,
        timeout=5,
    )
    assert not duplicate_saved, "Контакт №2 сохранён с телефоном контакта №1"


# Поле модели -> ключ в API -> кейс STD.
# Известным багом помечен только email: бэкенд отклоняет пустые name/lastName/phone/address
# (400, данные не меняются), а пустой email сохраняет.
CLEAR_FIELD_CASES = [
    pytest.param("name", "name", "TC-0028", id="name"),
    pytest.param("last_name", "lastName", "TC-0029", id="last_name"),
    pytest.param("email", "email", "TC-0030", id="email", marks=known_bug("EMAIL_NOT_REQUIRED")),
    pytest.param("phone", "phone", "TC-0031", id="phone"),
    pytest.param("address", "address", "TC-0032", id="address"),
]


@pytest.mark.regression
@allure.story("Clear required field")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, api_key, test_case", CLEAR_FIELD_CASES)
def test_edit_contact_clear_required_fields(authenticated_driver, auth_api, created_contact,
                                            field, api_key, test_case):
    """SRS F10–F14: если обязательное поле очищено, система не сохраняет невалидные данные."""
    allure.dynamic.tag(test_case)

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact.phone, Contact(**{field: ""}))

    empty_saved = eventually(
        lambda: _stored_contact(auth_api, created_contact.id).get(api_key) == "",
        timeout=5,
    )
    assert not empty_saved, f"Контакт сохранён с пустым обязательным полем '{field}'"
