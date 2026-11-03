"""Сквозной сценарий жизни контакта: создание -> изменение -> удаление.

В отличие от отдельных CRUD-тестов, здесь каждый шаг опирается на результат
предыдущего, а состояние после каждого действия сверяется через список контактов.
"""

import allure
import pytest

from data.data_generator import ContactGenerator

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _by_id(contacts: list[dict]) -> dict[str, dict]:
    return {c.get("id"): c for c in contacts}


@allure.epic("API Testing")
@allure.feature("Contacts CRUD")
@allure.story("Contact lifecycle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("API-CHECK-20")
def test_api_contact_lifecycle(auth_api):
    """POST -> список -> PUT -> список -> DELETE -> список."""
    contact = ContactGenerator.get_random_contact().to_api_payload()

    with allure.step("1. Создание: контакт появился в списке с отправленными данными"):
        before = _by_id(auth_api.get_contacts_list())
        response = auth_api.add_contact(contact)
        assert response.status_code == 200, f"Создание: {response.status_code} {response.text}"

        after_create = _by_id(auth_api.get_contacts_list())
        new_ids = set(after_create) - set(before)
        assert len(new_ids) == 1, f"Ожидался один новый контакт, появилось {len(new_ids)}"
        contact_id = new_ids.pop()
        stored = after_create[contact_id]
        assert {k: stored.get(k) for k in contact} == contact, f"Сохранено не то, что отправлено: {stored}"

    with allure.step("2. Изменение: обновлён именно этот контакт, другие не затронуты"):
        updated = {**ContactGenerator.get_random_contact().to_api_payload(), "id": contact_id}
        response = auth_api.update_contact(updated)
        assert response.status_code == 200, f"Изменение: {response.status_code} {response.text}"

        after_update = _by_id(auth_api.get_contacts_list())
        assert set(after_update) == set(after_create), "Изменение добавило или удалило контакты"
        assert {k: after_update[contact_id].get(k) for k in updated} == updated, (
            f"Сохранены не изменённые данные: {after_update[contact_id]}"
        )

    with allure.step("3. Удаление: контакта нет, остальные на месте"):
        response = auth_api.delete_contact(contact_id)
        assert response.status_code == 200, f"Удаление: {response.status_code} {response.text}"

        after_delete = _by_id(auth_api.get_contacts_list())
        assert contact_id not in after_delete, "Контакт остался в списке после удаления"
        assert set(after_delete) == set(after_update) - {contact_id}, "Удаление затронуло другие контакты"
