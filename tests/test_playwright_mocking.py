import allure
import pytest
from playwright.sync_api import Page

from models.contact import Contact
from pages.pw_contacts_page import PwContactsPage
from pages.pw_login_page import PwLoginPage
from utils.network_faults import CONTACTS

# Контакт, которого нет на бэкенде: браузер увидит его вместо реальных данных
FAKE = Contact(
    id="mocked-uuid-12345",
    name="Terminator",
    last_name="T-800",
    email="skynet@example.com",
    phone="0501234567",
    address="Cyberdyne Systems",
    description="I'll be back",
)


@pytest.mark.regression
@pytest.mark.playwright
@allure.epic("Playwright Testing")
@allure.feature("Network Interception")
@allure.story("Mocking Contacts List")
@allure.title("Изоляция UI: подмена ответа бэкенда (Mocking)")
def test_mock_contacts_list(page: Page, network_faults, temp_user):
    """UI корректно отрисовывает данные, которые вернул бэкенд.

    Ответ на GET /v1/contacts подменяется, поэтому тест проверяет только
    отрисовку и не зависит от реальных данных пользователя.
    """
    # Перехват включаем ДО логина: после него фронтенд сразу запросит список контактов.
    # Остальные методы (POST/PUT/DELETE) NetworkFaults пропускает на настоящий сервер
    faults = network_faults
    gets = faults.respond(CONTACTS, "GET", 200, {"contacts": [FAKE.to_api_payload()]})

    login_page = PwLoginPage(page)
    login_page.open()
    login_page.login(temp_user.user.email, temp_user.user.password)
    contacts = PwContactsPage(page)
    contacts.wait_opened()
    # Подмена реально сработала: без неё карточки FAKE не было бы, и тест упал бы на проверке
    # отрисовки, а не на причине — поэтому неприменённый перехват ловим как предусловие
    faults.wait_for_delivery(gets)

    contacts.check_card_visible(FAKE)
    shown = contacts.card_name(FAKE.phone)
    assert shown == FAKE.name, f"Карточка подменённого контакта показывает {shown!r}, в ответе бэкенда {FAKE.name!r}"

    contacts.open_details(FAKE.phone)
    contacts.check_details_show(FAKE)
