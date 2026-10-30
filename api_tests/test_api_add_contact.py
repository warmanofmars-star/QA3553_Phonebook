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
@allure.tag("TC-0018", "TC-0019")
@known_bug("DUPLICATE_CONTACT")
def test_api_add_contact_duplicate(auth_api):
    """Повторное создание контакта с теми же данными должно отклоняться с 409 (SRS T32, T45; Swagger)."""
    payload = ContactGenerator.get_random_contact().to_api_payload()

    res_first = auth_api.add_contact(payload)
    require(res_first.status_code == 200, f"Предусловие: первый контакт не создался: {res_first.text}")

    with allure.step("Повторная отправка тех же данных"):
        res_second = auth_api.add_contact(payload)

    assert_secure_error(res_second, 409)
