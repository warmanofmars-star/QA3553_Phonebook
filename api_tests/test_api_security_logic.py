"""
Безопасность и логика API: доступ к чужим данным (BOLA), mass assignment,
идемпотентность, реакция на неправильные запросы.

Принцип разделения:
  * Тест БЕЗОПАСНОСТИ проверяет главное — чужие данные не пострадали.
    Он без xfail и обязан покраснеть, если уязвимость появится.
  * Тест КОНТРАКТА проверяет точный код ответа по Swagger.
    Известные расхождения помечены known_bug.
Если смешать их в одном тесте, xfail на коде ответа спрячет и настоящую уязвимость.
"""

from dataclasses import replace

import allure
import pytest

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from utils.preconditions import require
from utils.validators import assert_secure_error

pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.regression]

NONEXISTENT_ID = "00000000-0000-0000-0000-000000000000"


def _create_contact_for(user):
    """Создаёт контакт у переданного пользователя (TempUser) и возвращает его с id."""
    contact = ContactGenerator.get_random_contact()
    response = user.api.add_contact(contact.to_api_payload())
    require(response.status_code == 200, f"Предусловие: контакт не создан: {response.text}")
    return replace(contact, id=user.api.find_contact_id(contact.phone))


def _get_contact(api, contact_id):
    """Контакт пользователя по id или None."""
    return next((c for c in api.get_contacts_list() if c.get("id") == contact_id), None)


# ==========================================
# BOLA: доступ к чужому контакту
# ==========================================
@allure.epic("API Security")
@allure.feature("BOLA (Broken Object Level Authorization)")
@allure.story("Delete other user's contact")
@allure.severity(allure.severity_level.BLOCKER)
def test_api_bola_cannot_delete_others_contact(temp_user, second_user):
    """Пользователь A не может удалить контакт пользователя B."""
    contact_b = _create_contact_for(second_user)

    with allure.step("Атака: A удаляет контакт B"):
        attack = temp_user.api.delete_contact(contact_b.id)

    # Главная проверка — данные B на месте. Именно это и есть защита от BOLA.
    with allure.step("Проверка: контакт B не удалён"):
        assert contact_b.id in second_user.api.get_contact_ids(), \
            "КРИТИЧНО (BOLA): пользователь A удалил контакт пользователя B!"

    # Вторичная проверка — сервер не рапортует об успехе и не раскрывает лишнего
    assert attack.status_code != 200, "Сервер ответил 200 на удаление чужого контакта"
    assert_secure_error(attack)


@allure.epic("API Security")
@allure.feature("BOLA (Broken Object Level Authorization)")
@allure.story("Update other user's contact")
@allure.severity(allure.severity_level.BLOCKER)
def test_api_bola_cannot_update_others_contact(temp_user, second_user):
    """Пользователь A не может изменить контакт пользователя B через PUT."""
    contact_b = _create_contact_for(second_user)

    with allure.step("Атака: A отправляет PUT с id контакта B и своими данными"):
        forged = ContactGenerator.get_random_contact().to_api_payload()
        forged["id"] = contact_b.id
        attack = temp_user.api.update_contact(forged)

    with allure.step("Проверка: данные контакта B не изменились"):
        stored = _get_contact(second_user.api, contact_b.id)
        assert stored is not None, "КРИТИЧНО (BOLA): контакт B исчез после PUT пользователя A!"
        assert stored.get("phone") == contact_b.phone, \
            "КРИТИЧНО (BOLA): пользователь A изменил контакт пользователя B!"

    assert attack.status_code != 200, "Сервер ответил 200 на изменение чужого контакта"
    assert_secure_error(attack)


@allure.epic("API Security")
@allure.feature("Mass Assignment")
@allure.story("Client-supplied id on create")
@allure.severity(allure.severity_level.CRITICAL)
def test_api_mass_assignment_foreign_id(temp_user, second_user):
    """В ContactDto (Swagger) есть поле id. Нельзя, чтобы клиент мог им управлять:
    создание контакта с id чужого контакта не должно перезаписать чужие данные."""
    contact_b = _create_contact_for(second_user)

    with allure.step("Атака: A создаёт контакт, подставив id контакта B"):
        forged = ContactGenerator.get_random_contact().to_api_payload()
        forged["id"] = contact_b.id
        temp_user.api.add_contact(forged)

    with allure.step("Проверка: контакт B не изменился"):
        stored = _get_contact(second_user.api, contact_b.id)
        assert stored is not None and stored.get("phone") == contact_b.phone, \
            "КРИТИЧНО: подставленный клиентом id перезаписал чужой контакт!"

    with allure.step("Проверка: у A контакт создан с новым id, выданным сервером"):
        assert contact_b.id not in temp_user.api.get_contact_ids(), \
            "Сервер принял id, переданный клиентом"


# ==========================================
# Контракт: код ответа для отсутствующего контакта
# ==========================================
@allure.epic("API Testing")
@allure.feature("Contract")
@allure.story("Contact not found -> 404")
@allure.severity(allure.severity_level.MINOR)
@known_bug("NOT_FOUND_400")
@pytest.mark.parametrize("scenario", ["foreign", "nonexistent"])
def test_api_delete_missing_contact_returns_404(temp_user, second_user, scenario):
    """Swagger: DELETE /v1/contacts/{id} -> 404 'Contact not found'.
    Для пользователя A чужой контакт — тоже 'не найден'."""
    contact_id = _create_contact_for(second_user).id if scenario == "foreign" else NONEXISTENT_ID

    response = temp_user.api.delete_contact(contact_id)
    assert_secure_error(response, 404)


# ==========================================
# Логика и устойчивость
# ==========================================
@allure.epic("API Logic")
@allure.feature("Idempotency")
@allure.story("Double DELETE operation")
@allure.severity(allure.severity_level.NORMAL)
def test_api_delete_idempotency(auth_api, created_contact):
    """Повторный DELETE того же контакта не должен ни падать, ни рапортовать об успехе.
    Точный код ответа проверяет test_api_delete_missing_contact_returns_404."""
    res_first = auth_api.delete_contact(created_contact.id)
    assert res_first.status_code == 200, f"Первое удаление не прошло: {res_first.text}"

    with allure.step("Повторная отправка DELETE на уже удалённый ресурс"):
        res_second = auth_api.delete_contact(created_contact.id)

    assert res_second.status_code < 500, f"Сервер упал на повторном удалении: {res_second.status_code}"
    assert res_second.status_code != 200, "Повторное удаление несуществующего контакта вернуло 200"
    assert_secure_error(res_second)


@allure.epic("API Security")
@allure.feature("HTTP Protocol")
@allure.story("Unsupported HTTP method")
@allure.severity(allure.severity_level.NORMAL)
def test_api_unsupported_method_is_rejected(auth_api, created_contact):
    """POST на эндпоинт, который принимает только DELETE, должен быть отклонён
    ошибкой клиента и не должен ничего удалить.
    Раньше тест ожидал именно 405, но в Swagger 405 не описан, а 403 от Spring Security —
    тоже корректный отказ. Поэтому проверяем суть, а не конкретную цифру."""
    with allure.step("Отправляем POST вместо DELETE на /v1/contacts/clear"):
        response = auth_api.request("POST", "/v1/contacts/clear")

    assert 400 <= response.status_code < 500, f"Ожидалась ошибка клиента 4xx, получено {response.status_code}"
    assert created_contact.id in auth_api.get_contact_ids(), "Запрос неподдерживаемым методом удалил контакты!"
    assert_secure_error(response)


@allure.epic("API Security")
@allure.feature("HTTP Protocol")
@allure.story("Unsupported Content-Type")
@allure.severity(allure.severity_level.NORMAL)
@known_bug("WRONG_CONTENT_TYPE_500")
def test_api_wrong_content_type_is_client_error(auth_api):
    """Тело text/plain вместо JSON — ошибка клиента, сервер должен ответить 4xx (в идеале 415), а не падать."""
    with allure.step("Отправляем обычный текст с заголовком text/plain вместо application/json"):
        response = auth_api.request(
            "POST", "/v1/contacts",
            data="Malicious plain text payload",
            headers={"Content-Type": "text/plain"},
        )

    assert 400 <= response.status_code < 500, \
        f"Ошибка клиента должна давать 4xx, а сервер ответил {response.status_code}"
    assert_secure_error(response)
