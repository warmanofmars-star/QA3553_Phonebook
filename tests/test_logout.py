import allure
import pytest

from pages.contacts_page import ContactsPage
from pages.login_page import LoginPage

pytestmark = [pytest.mark.ui, allure.epic("UI Testing"), allure.feature("Authentication")]


@pytest.mark.smoke
@allure.story("Logout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("TC-0010")
def test_logout_success(authenticated_driver):
    """Авторизованный пользователь может выйти из системы."""
    ContactsPage(authenticated_driver).sign_out()

    login_page = LoginPage(authenticated_driver)
    assert login_page.is_login_form_displayed(), "После выхода не появилась форма входа"
    assert not login_page.is_signed_in(timeout=1), "После выхода кнопка Sign Out осталась на экране"


@pytest.mark.regression
@pytest.mark.security
@allure.story("Anonymous access to contacts")
@allure.severity(allure.severity_level.CRITICAL)
def test_anonymous_user_redirected_to_login(driver):
    """Аноним, открывший /contacts напрямую, перенаправляется на вход и не видит контакты.

    Это проверка UX, а не защиты данных: настоящую защиту обеспечивает API
    (см. test_api_invalid_tokens) — фронтенд можно обойти, бэкенд нельзя.
    """
    contacts_page = ContactsPage(driver)
    contacts_page.open()

    assert contacts_page.is_url_contains("/login"), f"Нет редиректа на вход, текущий адрес: {driver.current_url}"
    assert LoginPage(driver).is_login_form_displayed(), "Форма входа не отображается"
    assert contacts_page.cards_count() == 0, "Анониму показаны карточки контактов"
