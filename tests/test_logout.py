import allure
from pages.contacts_page import ContactsPage
from pages.login_page import LoginPage
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


class TestLogout:

    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout_success(self, authenticated_driver):
        """Проверка: Авторизованный пользователь может успешно выйти из системы."""
        logger.info("--- ЗАПУСК ТЕСТА: test_logout_success ---")
        contacts_page = ContactsPage(authenticated_driver)
        login_page = LoginPage(authenticated_driver)

        logger.info("ПОДГОТОВКА: Тест запущен под АВТОРИЗОВАННЫМ пользователем (сработала фикстура)")

        # 1. Нажимаем Sign Out (метод подтянется из BasePage!)
        logger.info("ШАГ 1: Нажимаем кнопку 'Sign Out' в навигационном меню")
        contacts_page.click_sign_out_button()

        # 2. Проверяем, что нас выкинуло на страницу логина
        logger.info("ПРОВЕРКА: Убеждаемся, что система разлогинила пользователя и появилась кнопка Login")
        assert login_page.is_login_button_visible(), "Ошибка: Кнопка Login не появилась после выхода из системы!"
        logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")

    @allure.severity(allure.severity_level.CRITICAL)
    def test_logout_security_redirect(self, driver):
        """Проверка безопасности: Неавторизованный пользователь не может открыть страницу /contacts."""
        logger.info("--- ЗАПУСК ТЕСТА: test_logout_security_redirect ---")

        # Передаем driver (без авторизации!), а не authenticated_driver
        contacts_page = ContactsPage(driver)
        login_page = LoginPage(driver)

        logger.info("ПОДГОТОВКА: Тест запущен под АНОНИМНЫМ пользователем (чистый driver)")

        # 1. Пытаемся напрямую перейти по URL /contacts
        logger.info("ШАГ 1: Пытаемся напрямую (в обход авторизации) открыть защищенный URL /contacts")
        contacts_page.open()

        # 2. Система должна автоматически перенаправить нас на страницу логина
        logger.info(
            "ПРОВЕРКА: Ожидаем принудительный редирект. Убеждаемся, что мы на странице авторизации (видна кнопка Login)")
        assert login_page.is_login_button_visible(), "УЯЗВИМОСТЬ: Система пустила анонима на страницу контактов!"
        logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН (Уязвимость не обнаружена) ---")