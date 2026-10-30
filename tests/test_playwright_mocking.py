import allure
import pytest
from playwright.sync_api import Page, Route, expect

from pages.pw_login_page import PwLoginPage

# Ответ бэкенда, который увидит браузер вместо реальных данных
FAKE_CONTACTS = {
    "contacts": [
        {
            "id": "mocked-uuid-12345",
            "name": "Terminator",
            "lastName": "T-800",
            "email": "skynet@example.com",
            "phone": "0501234567",
            "address": "Cyberdyne Systems",
            "description": "I'll be back",
        }
    ]
}


@pytest.mark.regression
@pytest.mark.playwright
@allure.epic("Playwright Testing")
@allure.feature("Network Interception")
@allure.story("Mocking Contacts List")
@allure.title("Изоляция UI: подмена ответа бэкенда (Mocking)")
def test_mock_contacts_list(page: Page, temp_user):
    """UI корректно отрисовывает данные, которые вернул бэкенд.

    Ответ на GET /v1/contacts подменяется, поэтому тест проверяет только
    отрисовку и не зависит от реальных данных пользователя.
    """
    def handle_route(route: Route):
        if route.request.method == "GET":
            route.fulfill(json=FAKE_CONTACTS, status=200)
        else:
            route.continue_()  # POST/PUT/DELETE уходят на настоящий сервер

    # Перехват включаем ДО логина: после него фронтенд сразу запросит список контактов
    page.route("**/v1/contacts", handle_route)

    login_page = PwLoginPage(page)
    login_page.open()
    login_page.login(temp_user.user.email, temp_user.user.password)

    fake = FAKE_CONTACTS["contacts"][0]
    with allure.step("Проверка компактной карточки в списке"):
        expect(page.get_by_text(fake["name"])).to_be_visible()
        expect(page.get_by_text(fake["phone"])).to_be_visible()

    with allure.step("Открытие деталей контакта"):
        page.get_by_text(fake["name"]).click()

    with allure.step("Проверка детальной информации"):
        # expect() сам ждёт появления элемента (по умолчанию до 5 с) — wait_for() не нужен
        for value in (fake["lastName"], fake["email"], fake["address"], fake["description"]):
            expect(page.get_by_text(value, exact=False)).to_be_visible()
