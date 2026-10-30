import allure
import pytest
from selenium.webdriver.support.wait import WebDriverWait
from pages.contacts_page import ContactsPage
from utils.logger import get_logger
from utils.preconditions import require

logger = get_logger("TEST")


# ==========================================
# 1. ТЕСТ ОДИНОЧНОГО УДАЛЕНИЯ
# ==========================================

@pytest.mark.hybrid
@pytest.mark.smoke
@pytest.mark.ui
@allure.epic("Hybrid Testing")
@allure.feature("Contacts Management")
@allure.story("API Setup -> UI Delete -> UI Assert")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_contact(authenticated_driver, created_contact):
    """Контакт создаётся через API (фикстура created_contact), удаляется через UI."""
    logger.info("--- ЗАПУСК ГИБРИДНОГО ТЕСТА: test_delete_contact ---")
    contact = created_contact

    # Инициализируем страницу ДО ее использования
    contacts_page = ContactsPage(authenticated_driver)

    with allure.step("UI SCENARIO: Открываем карточку и удаляем контакт"):
        contacts_page.open()
        logger.info(f"ШАГ 1: Кликаем по карточке контакта ({contact.phone})")
        contacts_page.open_contact_details(contact.phone)
        logger.info("ШАГ 2: Нажимаем кнопку Remove")
        contacts_page.click_remove_button()

    with allure.step(f"UI ASSERT: Проверяем, что карточка исчезла"):
        assert contacts_page.is_contact_deleted(contact.phone), \
            f"Ошибка: Карточка с телефоном {contact.phone} не удалилась из списка!"
        logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# 2. УДАЛЕНИЕ ВСЕХ КОНТАКТОВ ЧЕРЕЗ UI (по одному)
# ==========================================
@pytest.mark.regression
@pytest.mark.ui
@allure.epic("UI Testing")
@allure.feature("Contacts Management")
@allure.story("Mass Delete Utilities")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.hybrid
def test_delete_all_contacts(authenticated_driver, auth_api, create_contact):
    """Удаление всех контактов пользователя через UI, по одному.

    Раньше тест запускался на новом sandbox-пользователе без контактов и проходил
    всегда: удалять было нечего. Теперь контакты создаются заранее через API.
    Предохранитель ALLOW_MASS_DELETE больше не нужен: пользователь одноразовый.
    """
    logger.info("--- ЗАПУСК ТЕСТА: test_delete_all_contacts ---")
    phones = [create_contact().phone for _ in range(3)]
    contacts_page = ContactsPage(authenticated_driver)

    contacts_page.open()
    # Ждём, пока React отрисует карточки. Без этого delete_all_contacts() мог бы
    # увидеть пустой список (ещё не загрузился) и сразу выйти — тест снова стал бы "пустым".
    for phone in phones:
        contacts_page.contact_card_visible(phone)
    require(contacts_page.get_all_contacts_count() == len(phones),
            f"Предусловие: на странице должно быть {len(phones)} карточки")

    contacts_page.delete_all_contacts()

    final_count = contacts_page.get_all_contacts_count()
    assert final_count == 0, f"Ошибка: Ожидалось 0 карточек, но осталось {final_count}!"
    assert auth_api.get_contact_ids() == [], "Карточки пропали из UI, но контакты остались на бэкенде!"


# ==========================================
# 3. МНОЖЕСТВЕННОЕ ТОЧЕЧНОЕ УДАЛЕНИЕ
# ==========================================

@pytest.mark.hybrid
@pytest.mark.regression
@pytest.mark.ui
@allure.epic("Hybrid Testing")
@allure.feature("Contacts Management")
@allure.story("API Setup -> UI Multiple Delete")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_multiple_contacts(authenticated_driver, create_contact):
    """Проверка последовательного удаления нескольких конкретных контактов"""
    logger.info("--- ЗАПУСК ГИБРИДНОГО ТЕСТА: test_delete_multiple_contacts ---")
    contacts_page = ContactsPage(authenticated_driver)

    # ПРЕДУСЛОВИЕ ЧЕРЕЗ API: фабрика create_contact создаёт контакты у того же
    # temp_user, под которым залогинен браузер
    phones_to_delete = [create_contact().phone for _ in range(2)]

    # ==========================================
    # ШАГИ ТЕСТА ЧЕРЕЗ UI
    # ==========================================
    with allure.step(f"UI SCENARIO: Точечное удаление контактов из списка: {phones_to_delete}"):
        contacts_page.open()

        logger.info("СИНХРОНИЗАЦИЯ: Ждем, пока React отрисует массив карточек в DOM")
        WebDriverWait(authenticated_driver, 10).until(
            lambda d: len(d.find_elements(*contacts_page.CONTACT_CARDS)) > 0,
            message="Список контактов так и не загрузился!"
        )

        # Убеждаемся, что наши карточки подгрузились
        contacts_page.contact_card_visible(phones_to_delete[0])

        # Удаляем контакты селениумом (без подсчета общего количества)
        contacts_page.delete_specific_contacts(phones_to_delete)

    # ==========================================
    # ПРОВЕРКА
    # ==========================================
    with allure.step("UI ASSERT: Проверяем, что удаленные контакты больше не отображаются"):
        for phone in phones_to_delete:
            assert contacts_page.is_contact_deleted(phone), \
                f"Ошибка: Карточка с телефоном {phone} не удалилась из списка!"

    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")