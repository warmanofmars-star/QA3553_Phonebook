import allure
import pytest

from data.known_bugs import known_bug


@pytest.mark.smoke
@pytest.mark.api
@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Delete Contact")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_delete_contact(auth_api, created_contact):
    response_delete = auth_api.delete_contact(created_contact.id)
    assert response_delete.status_code == 200, \
        f"API не смог удалить контакт: {response_delete.status_code} {response_delete.text}"

    assert created_contact.id not in auth_api.get_contact_ids(), "БАГ: Контакт не удалился из базы данных!"


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.security
@allure.epic("API Security")
@allure.feature("BFLA (Broken Function Level Authorization)")
@allure.story("Customer cannot delete all contacts")
@allure.severity(allure.severity_level.CRITICAL)
@known_bug("CUSTOMER_CAN_CLEAR_ALL")
def test_api_customer_cannot_clear_all_contacts(auth_api, create_contact):
    """SRS, раздел 2, модуль 'Delete all contact': Customer — Can't, только Manager.

    Раньше здесь был тест, проверявший ОБРАТНОЕ (что удаление проходит успешно),
    да ещё и на пустом списке: у нового sandbox-пользователя контактов нет,
    поэтому "все удалены" выполнялось всегда. Теперь контакты создаются заранее.
    """
    seeded_ids = {create_contact().id for _ in range(2)}

    with allure.step("Обычный пользователь вызывает DELETE /v1/contacts/clear"):
        response = auth_api.clear_contacts()

    # Главное — данные на месте; код ответа вторичен (SRS его не задаёт)
    remaining = seeded_ids & set(auth_api.get_contact_ids())
    assert remaining == seeded_ids, \
        f"Обычный пользователь удалил все контакты (удалено {len(seeded_ids - remaining)} из {len(seeded_ids)})"
    assert response.status_code in (401, 403), \
        f"Ожидался отказ в доступе (401/403), получено {response.status_code}"
