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


def _describe_saved(entered: Contact, saved: dict) -> str:
    """Что ввели и что лежит на бэкенде — по каждому введённому полю."""
    entered_payload = {key: value for key, value in entered.to_api_payload().items() if value is not None}
    return "; ".join(f"{key}: ввели {value!r}, на бэкенде {saved.get(key)!r}" for key, value in entered_payload.items())


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
    # Новое значение гарантированно отличается от старого: иначе сохранение того же
    # значения было бы неотличимо от поломки ("изменения не сохранились")
    new_value = getattr(ContactGenerator.get_contact_different_from(created_contact), field)
    change = Contact(**{field: new_value})
    expected = replace(created_contact, **{field: new_value})

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact, change)

    with allure.step("Проверить через API, что изменилось только нужное поле"):
        before = created_contact.to_api_payload()
        changed = eventually(lambda: _saved_fields(auth_api, created_contact) != before, timeout=5)
        actual = _saved_fields(auth_api, created_contact)
        assert changed, f"Изменение поля {field} не сохранилось на бэкенде: {_describe_saved(change, actual)}"
        assert actual == expected.to_api_payload(), (
            f"Сохранённые данные отличаются от ожидаемых:\n{actual}\n!=\n{expected.to_api_payload()}"
        )


@pytest.mark.regression
@allure.story("Edit all fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("TC-0027")
@known_bug("EDIT_DESCRIPTION_BROKEN")
def test_edit_contact_all_fields(authenticated_driver, auth_api, created_contact):
    """Все поля контакта меняются за одно редактирование, каждое сохраняется в своё поле."""
    # Каждое поле гарантированно отличается от старого значения
    expected = replace(ContactGenerator.get_contact_different_from(created_contact), id=created_contact.id)

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact, expected)

    assert contacts_page.is_card_displayed(expected.phone), "Изменённый контакт не появился в списке"

    with allure.step("Проверить через API, что все поля сохранены верно"):
        updated = eventually(
            lambda: _stored_contact(auth_api, created_contact.id).get("phone") == expected.phone,
            timeout=5,
        )
        actual = _saved_fields(auth_api, created_contact)
        assert updated, f"Изменения не сохранились на бэкенде: {_describe_saved(expected, actual)}"
        assert actual == expected.to_api_payload(), (
            f"Сохранённые данные отличаются от введённых:\n{actual}\n!=\n{expected.to_api_payload()}"
        )


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
    contacts_page.edit_contact(contact_2, Contact(phone=contact_1.phone), expect_saved=False)  # только телефон

    duplicate_saved = eventually(
        lambda: _stored_contact(auth_api, contact_2.id).get("phone") == contact_1.phone,
        timeout=5,
    )
    assert not duplicate_saved, "Контакт №2 сохранён с телефоном контакта №1"


@pytest.mark.regression
@allure.story("Edit with duplicate email")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0034")
@known_bug("DUPLICATE_CONTACT")
def test_edit_contact_duplicate_email(authenticated_driver, auth_api, create_contact):
    """SRS T70: при редактировании email не должен повторять email другого контакта."""
    contact_1 = create_contact()
    contact_2 = create_contact()

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(contact_2, Contact(email=contact_1.email), expect_saved=False)  # только email

    duplicate_saved = eventually(
        lambda: _stored_contact(auth_api, contact_2.id).get("email") == contact_1.email,
        timeout=5,
    )
    assert not duplicate_saved, "Контакт №2 сохранён с email контакта №1"


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
def test_edit_contact_clear_required_fields(authenticated_driver, auth_api, created_contact, field, api_key, test_case):
    """SRS F10–F14: если обязательное поле очищено, система не сохраняет невалидные данные."""
    allure.dynamic.tag(test_case)

    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact, Contact(**{field: ""}), expect_saved=False)

    empty_saved = eventually(
        lambda: _stored_contact(auth_api, created_contact.id).get(api_key) == "",
        timeout=5,
    )
    assert not empty_saved, f"Контакт сохранён с пустым обязательным полем '{field}'"


@pytest.mark.regression
@allure.story("Blank address")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0033")
def test_edit_contact_blank_address(authenticated_driver, auth_api, created_contact):
    """SRS T72, F14: адрес из одних пробелов — это blank, система не сохраняет такие данные.

    Пустой адрес проверяет TC-0032, здесь — пробелы: формально поле заполнено, но по T72
    это blank. В ожидаемом результате TC-0033 в STD упомянуто поле Name — это копипаст
    из SRS, где все F10–F14 заканчиваются словами "to the name field". Тест следует
    смыслу F14 и T72: проверяем адрес.
    """
    contacts_page = ContactsPage(authenticated_driver)
    contacts_page.open()
    contacts_page.edit_contact(created_contact, Contact(address="   "), expect_saved=False)

    address_changed = eventually(
        lambda: _stored_contact(auth_api, created_contact.id).get("address") != created_contact.address,
        timeout=5,
    )
    saved = _stored_contact(auth_api, created_contact.id).get("address")
    assert not address_changed, f"Адрес изменился: было {created_contact.address!r}, сохранено {saved!r}"
