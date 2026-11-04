import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from schemas.contact_schemas import MESSAGE_RESPONSE_SCHEMA
from utils.preconditions import require
from utils.validators import assert_json_schema, assert_secure_error


@pytest.mark.smoke
@pytest.mark.api
@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("API-CHECK-1", "API-CHECK-2", "API-CHECK-3")
def test_api_add_contact(auth_api):
    contact = ContactGenerator.get_random_contact()

    response = auth_api.add_contact(contact.to_api_payload())
    assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}: {response.text}"
    assert_json_schema(response.json(), MESSAGE_RESPONSE_SCHEMA, "Ответ на создание контакта")


@pytest.mark.regression
@pytest.mark.api
@allure.epic("API Testing")
@allure.feature("Contacts Validation")
@allure.story("Create Duplicate Contact")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("API-CHECK-11", "API-CHECK-13")
@known_bug("DUPLICATE_CONTACT")
# Повторяется ровно одно поле, остальные данные нового контакта уникальны:
# так отказ сервера указывает на конкретное правило — T32 (email) или T45 (телефон)
@pytest.mark.parametrize(
    "field",
    [
        pytest.param("email", id="email", marks=allure.tag("TC-0018", "SRS-T32")),
        pytest.param("phone", id="phone", marks=allure.tag("TC-0019", "SRS-T45")),
    ],
)
def test_api_add_contact_duplicate(auth_api, field):
    """Контакт, повторяющий email или телефон ранее созданного, не сохраняется,
    а сервер отвечает 409 (SRS T32, T45; Swagger: 409 Duplicate contact fields)."""
    original = ContactGenerator.get_random_contact().to_api_payload()
    res_first = auth_api.add_contact(original)
    require(res_first.status_code == 200, f"Предусловие: первый контакт не создался: {res_first.text}")

    duplicate = {**ContactGenerator.get_random_contact().to_api_payload(), field: original[field]}
    with allure.step(f"Создание второго контакта с тем же полем {field}"):
        res_second = auth_api.add_contact(duplicate)

    # Сначала состояние: главное — дубль не сохранён; код ответа вторичен
    same_value = [c for c in auth_api.get_contacts_list() if c.get(field) == original[field]]
    assert len(same_value) == 1, (
        f"Сохранён второй контакт с тем же {field} {original[field]!r} (ответ {res_second.status_code})"
    )
    assert_secure_error(res_second, 409)
