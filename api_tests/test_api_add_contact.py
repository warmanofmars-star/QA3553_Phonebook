import allure
import pytest
from data.data_generator import ContactGenerator
from utils.logger import get_logger

logger = get_logger("API")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_add_contact(auth_api):
    contact = ContactGenerator.get_random_contact()

    # Вся магия сессий: мы просто передаем payload, токен подтянется сам!
    response = auth_api.add_contact(contact.to_api_payload())

    if response.status_code == 200:
        logger.info(f"[POST УСПЕХ] Контакт {contact.name} {contact.last_name} успешно создан!")
    else:
        logger.error(f"[POST ОШИБКА] Сервер вернул: {response.status_code} - {response.text}")
        pytest.fail("API не смог создать контакт")


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Create Contact without Name")
@allure.severity(allure.severity_level.NORMAL)
def test_api_add_contact_missing_required_field(auth_api):
    contact = ContactGenerator.get_random_contact()
    contact_payload = contact.to_api_payload()
    del contact_payload["name"]

    response = auth_api.add_contact(contact_payload)

    if response.status_code == 400:
        logger.info("[POST УСПЕХ (Негативный)] Сервер корректно отклонил контакт без имени (400 Bad Request)")
    else:
        logger.error(f"[POST БАГ] Сервер принял невалидный контакт! Статус: {response.status_code} - {response.text}")
        pytest.fail("БАГ БЭКЕНДА: Сервер принял контакт без имени!")


@allure.epic("API Testing")
@allure.feature("Contacts Validation")
@allure.story("Create Duplicate Contact")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG BACKEND: Сервер возвращает 200 вместо 409 при дубликате (Swagger врет)")
def test_api_add_contact_duplicate(auth_api):
    contact = ContactGenerator.get_random_contact()
    payload = contact.to_api_payload()

    res_first = auth_api.add_contact(payload)
    assert res_first.status_code == 200, "Предусловие сломалось: первый контакт не создался"

    res_second = auth_api.add_contact(payload)

    if res_second.status_code == 409:
        logger.info("[POST УСПЕХ (Негативный)] Сервер корректно заблокировал дубликат (409 Conflict)")
    else:
        logger.error(
            f"[POST БАГ] Сервер позволил создать дубликат! Статус: {res_second.status_code} - {res_second.text}")
        pytest.fail("БАГ БЭКЕНДА: Сервер позволил создать дубликат!")