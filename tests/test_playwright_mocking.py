import os
import allure
from playwright.sync_api import Page, Route
from pages.pw_login_page import PwLoginPage

VALID_EMAIL = os.getenv("USER_EMAIL")
VALID_PASSWORD = os.getenv("USER_PASSWORD")


@allure.epic("Playwright Testing")
@allure.feature("Network Interception")
@allure.story("Mocking Contacts List")
@allure.title("Изоляция UI: Подмена ответа бэкенда (Mocking)")
def test_mock_contacts_list(page: Page):
    # 1. Готовим фейковый ответ, который мы отдадим браузеру вместо реальной БД
    fake_response = {
        "contacts": [
            {
                "id": "mocked-uuid-12345",
                "name": "Terminator",
                "lastName": "T-800",
                "email": "skynet@gmail.com",
                "phone": "0501234567",
                "address": "Cyberdyne Systems",
                "description": "I'll be back"
            }
        ]
    }

    # 2. ПЕРЕХВАТ СЕТИ: Говорим Playwright ловить ВСЕ GET-запросы к /v1/contacts
    # и моментально отдавать наш fake_response со статусом 200 OK
    def handle_route(route: Route):
        if route.request.method == "GET":
            route.fulfill(json=fake_response, status=200)
        else:
            # Если это POST/PUT/DELETE, пропускаем запрос к реальному серверу
            route.continue_()

    # Включаем прослушку сети ДО того, как фронтенд начнет делать запросы
    page.route("**/v1/contacts", handle_route)

    # 3. Выполняем обычный UI-логин
    login_page = PwLoginPage(page)
    login_page.open()
    login_page.login(VALID_EMAIL, VALID_PASSWORD)

    # 4. После логина React сделает запрос за списком контактов.
    # Но сработает наша ловушка, и UI получит Терминатора!

    with allure.step("Проверка рендера компактной карточки (Mock)"):
        # Ждем появления базовой инфы на карточке слева
        page.locator("text=Terminator").wait_for(state="visible")
        page.locator("text=0501234567").wait_for(state="visible")

    with allure.step("Открытие деталей контакта"):
        # Кликаем по карточке, чтобы справа открылась панель деталей
        page.locator("text=Terminator").click()

    with allure.step("Проверка рендера детальной информации"):
        # Теперь фамилия, email и адрес должны быть видны на экране
        page.locator("text=T-800").wait_for(state="visible")
        page.locator("text=skynet@gmail.com").wait_for(state="visible")
        page.locator("text=Cyberdyne Systems").wait_for(state="visible")
        page.locator("text=I'll be back").wait_for(state="visible")