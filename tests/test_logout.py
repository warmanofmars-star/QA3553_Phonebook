import allure
from pages.contacts_page import ContactsPage
from pages.login_page import LoginPage


class TestLogout:

    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout_success(self, authenticated_driver):
        """Проверка: Авторизованный пользователь может успешно выйти из системы."""
        contacts_page = ContactsPage(authenticated_driver)
        login_page = LoginPage(authenticated_driver)

        # 1. Нажимаем Sign Out (метод подтянется из BasePage!)
        contacts_page.click_sign_out_button()

        # 2. Проверяем, что нас выкинуло на страницу логина
        assert login_page.is_login_button_visible(), "Ошибка: Кнопка Login не появилась после выхода из системы!"

    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout_security_redirect(self, driver):
        """Проверка безопасности: Неавторизованный пользователь не может открыть страницу /contacts."""
        # Передаем driver (без авторизации!), а не authenticated_driver
        contacts_page = ContactsPage(driver)
        login_page = LoginPage(driver)

        # 1. Пытаемся напрямую перейти по URL /contacts
        contacts_page.open()

        # 2. Система должна автоматически перенаправить нас на страницу логина
        assert login_page.is_login_button_visible(), "УЯЗВИМОСТЬ: Система пустила анонима на страницу контактов!"