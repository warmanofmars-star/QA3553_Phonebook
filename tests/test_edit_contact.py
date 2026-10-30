import pytest
import allure
from pages.add_contact_page import ContactPage
from pages.contacts_page import ContactsPage
from data.data_generator import ContactGenerator
from models.contact import Contact
from data.known_bugs import known_bug
from utils.waits import eventually
from utils.logger import get_logger

# Создаем логгер для тестов
logger = get_logger("TEST")


# ==========================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==========================================

@pytest.mark.smoke
@pytest.mark.ui
@allure.severity(allure.severity_level.CRITICAL)
def test_edit_contact_positive(authenticated_driver):
    logger.info("--- ЗАПУСК ТЕСТА: test_edit_contact_positive ---")
    add_page = ContactPage(authenticated_driver)
    contacts_page = ContactsPage(authenticated_driver)

    # 1. ПРЕДУСЛОВИЕ: Создаем исходный контакт
    logger.info("ПОДГОТОВКА: Создаем исходный (старый) контакт")
    old_contact = ContactGenerator.get_random_contact()
    add_page.open()
    add_page.fill_contact_form(old_contact)
    add_page.submit_contact()
    contacts_page.contact_card_visible(old_contact.phone)  # Ждем авто-редирект

    # 2. Подготовка: Генерируем новые данные для замены
    logger.info("ПОДГОТОВКА: Генерируем новые данные для замены")
    new_contact = ContactGenerator.get_random_contact()

    # 3. ШАГИ ТЕСТА
    logger.info(f"ШАГ 1: Открываем карточку старого контакта (тел: {old_contact.phone}) и жмем Edit")
    contacts_page.open_contact_details(old_contact.phone)  # Открываем старую карточку
    contacts_page.click_edit_button()  # Жмем Edit

    logger.info(f"ШАГ 2: Вводим новые данные (имя: {new_contact.name}) и сохраняем")
    contacts_page.edit_contact_form(new_contact)  # Вводим новые данные
    contacts_page.click_save_edit_button()  # Сохраняем

    # 4. ПРОВЕРКА
    logger.info("ПРОВЕРКА 1: Убеждаемся, что измененный контакт появился в списке слева")
    assert contacts_page.contact_card_visible(new_contact.phone), "Измененный контакт не появился в списке слева!"

    # Снова открываем детали и жмем Edit, чтобы увидеть форму с сохраненными данными
    logger.info("ШАГ 3: Снова открываем детали измененного контакта и жмем Edit для строгой проверки полей")
    contacts_page.open_contact_details(new_contact.phone)
    contacts_page.click_edit_button()

    # Забираем данные ТОЧНО из своих полей!
    logger.info("ШАГ 4: Считываем сохраненные значения прямо из инпутов формы (Senior подход)")
    saved_contact = contacts_page.get_contact_data_from_form()

    # Точечные жесткие проверки (Строгое равенство!)
    logger.info("ПРОВЕРКА 2: Строго сравниваем сохраненные данные с теми, что мы отправляли")
    assert saved_contact.name == new_contact.name, f"Баг маппинга! Имя съехало. Ожидали {new_contact.name}, получили {saved_contact.name}"
    assert saved_contact.last_name == new_contact.last_name, "Баг маппинга! Фамилия сохранилась не туда!"
    assert saved_contact.email == new_contact.email, "Баг маппинга! Email сохранился не туда!"
    logger.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЕН ---")


# ==========================================
# НЕГАТИВНЫЕ ТЕСТЫ
# ==========================================
# Общий принцип: предусловия создаются через API (fixtures create_contact),
# действие — через UI, результат проверяется через API с ожиданием eventually().
# Требования F10–F14 звучат как "система не сохраняет невалидные данные",
# поэтому проверяем именно сохранение, а не то, закрылась ли форма.


def _stored_contact(api, contact_id):
    """Контакт в том виде, в каком он сохранён на бэкенде."""
    return next((c for c in api.get_contacts_list() if c.get("id") == contact_id), {})


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.hybrid
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("TC-0035")
@known_bug("DUPLICATE_CONTACT")
def test_edit_contact_duplicate_phone(authenticated_driver, auth_api, create_contact):
    """SRS T83: при редактировании телефон не должен повторять телефон другого контакта."""
    contact_1 = create_contact()
    contact_2 = create_contact()
    contacts_page = ContactsPage(authenticated_driver)

    logger.info(f"ШАГ 1: Меняем телефон контакта №2 на телефон контакта №1 ({contact_1.phone})")
    contacts_page.open()
    contacts_page.open_contact_details(contact_2.phone)
    contacts_page.click_edit_button()
    contacts_page.edit_contact_form(Contact(phone=contact_1.phone))  # меняем только телефон
    contacts_page.click_save_edit_button()

    logger.info("ПРОВЕРКА: телефон-дубликат не должен сохраниться")
    duplicate_saved = eventually(
        lambda: _stored_contact(auth_api, contact_2.id).get("phone") == contact_1.phone,
        timeout=5,
    )
    assert not duplicate_saved, "Контакт №2 сохранён с телефоном контакта №1"


# Поле модели -> ключ в API -> кейс STD.
# Только email помечен известным багом: проверка через API показала, что бэкенд
# отклоняет пустые name/lastName/phone/address (400, данные не меняются),
# а пустой email сохраняет. Раньше xfail стоял на всех пяти полях, потому что
# тест проверял "закрылась ли форма", а не "сохранились ли данные".
CLEAR_FIELD_CASES = [
    pytest.param("name", "name", "TC-0028", id="name"),
    pytest.param("last_name", "lastName", "TC-0029", id="last_name"),
    pytest.param("email", "email", "TC-0030", id="email", marks=known_bug("EMAIL_NOT_REQUIRED")),
    pytest.param("phone", "phone", "TC-0031", id="phone"),
    pytest.param("address", "address", "TC-0032", id="address"),
]


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.hybrid
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, api_key, test_case", CLEAR_FIELD_CASES)
def test_edit_contact_clear_required_fields(authenticated_driver, auth_api, created_contact,
                                            field, api_key, test_case):
    """SRS F10–F14: если обязательное поле очищено, система не сохраняет невалидные данные."""
    allure.dynamic.tag(test_case)
    contacts_page = ContactsPage(authenticated_driver)

    logger.info(f"ШАГ 1: Открываем контакт и очищаем поле '{field}'")
    contacts_page.open()
    contacts_page.open_contact_details(created_contact.phone)
    contacts_page.click_edit_button()
    contacts_page.edit_contact_form(Contact(**{field: ""}))
    contacts_page.click_save_edit_button()

    logger.info("ПРОВЕРКА: пустое значение не должно сохраниться на бэкенде")
    empty_saved = eventually(
        lambda: _stored_contact(auth_api, created_contact.id).get(api_key) == "",
        timeout=5,
    )
    assert not empty_saved, f"Контакт сохранён с пустым обязательным полем '{field}'"
