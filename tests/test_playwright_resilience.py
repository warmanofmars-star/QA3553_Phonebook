"""Поведение UI при сбоях бэкенда: ответ 500/401, обрыв сети, медленный ответ, двойной клик.

Сбои подставляет перехват сети Playwright (utils/network_faults.py), данные — настоящие:
пользователь и контакты создаются через API, результат на бэкенде проверяется через API.

SRS о поведении при сбоях ничего не говорит (нефункциональные требования — Nil),
поэтому тесты делятся на три категории:
  * защита хорошего поведения — обычные тесты: приложение уже ведёт себя правильно,
    и это не должно сломаться (например, сбой PUT не показывает несохранённое значение);
  * наблюдения (data/observations.py, тег OBS-<KEY>) — плохое поведение, о котором
    требований нет; ожидание обосновано общими принципами (UX, семантика HTTP).
    Строгий xfail: исправят поведение — тест упадёт с XPASS;
  * известный баг (data/known_bugs.py) — нарушение требования SRS: двойная отправка
    создаёт дубль, а SRS T45 запрещает повторять телефон.

Негативные проверки ("значение НЕ изменилось", "ошибки НЕТ") ждут SETTLE_MS после
ответа на перехваченный запрос: даём приложению время "сделать плохое".
"""

import allure
import pytest
from playwright.sync_api import Page

from data.data_generator import ContactGenerator
from data.known_bugs import known_bug
from data.observations import observation
from pages.pw_add_contact_page import PwAddContactPage
from pages.pw_contacts_page import PwContactsPage
from pages.pw_feedback import PwFeedback
from pages.pw_login_page import PwLoginPage
from utils.network_faults import CONTACT_BY_ID, CONTACTS, NetworkFaults

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.regression,
    allure.epic("Playwright Testing"),
    allure.feature("Backend failures"),
]

SETTLE_MS = 2000  # время приложению отреагировать на ответ (для негативных проверок)
ERROR_WAIT_MS = 5000  # сколько ждём сообщения об ошибке
LOADING_LIMIT_MS = 10000  # "разумное время" загрузки списка
SECOND_CLICK_MS = 1000  # время, за которое второй клик успел бы отправить второй запрос


def _login(page: Page, temp_user) -> PwContactsPage:
    login_page = PwLoginPage(page)
    login_page.open()
    login_page.login(temp_user.user.email, temp_user.user.password)
    contacts = PwContactsPage(page)
    contacts.wait_opened()
    return contacts


def _stored(api, contact_id: str) -> dict | None:
    return next((c for c in api.get_contacts_list() if c.get("id") == contact_id), None)


def _add_contact_via_form(page: Page, temp_user, *, double_click: bool = False):
    """Вход, форма добавления, Save. Возвращает введённый контакт и страницу формы."""
    _login(page, temp_user)
    add_page = PwAddContactPage(page)
    add_page.open_from_menu()
    contact = ContactGenerator.get_random_contact()
    add_page.fill_form(contact)
    if double_click:
        add_page.double_click_save()
    else:
        add_page.save()
    return contact, add_page


# ==========================================
# ЗАЩИТА ХОРОШЕГО ПОВЕДЕНИЯ
# ==========================================
@allure.story("Good behaviour")
@allure.title("Сбой PUT: карточка и бэкенд хранят старое значение")
def test_put_failure_keeps_old_value(page: Page, temp_user, created_contact, auth_api):
    faults = NetworkFaults(page)
    puts = faults.respond(CONTACTS, "PUT", 500)
    contacts = _login(page, temp_user)
    contacts.open_details(created_contact.phone)

    contacts.edit_name("Changed" + created_contact.name)
    faults.wait_for_requests(puts)
    page.wait_for_timeout(SETTLE_MS)

    shown = contacts.card_name(created_contact.phone)
    assert shown == created_contact.name, f"После сбоя PUT карточка показывает {shown!r}, ожидалось старое имя"
    stored = _stored(auth_api, created_contact.id)
    assert stored, "Контакт пропал с бэкенда после сбоя PUT"
    assert stored["name"] == created_contact.name, f"На бэкенде изменилось имя: {stored}"


@allure.story("Good behaviour")
@allure.title("Сбой DELETE: карточка осталась, контакт на бэкенде на месте")
def test_delete_failure_keeps_contact(page: Page, temp_user, created_contact, auth_api):
    faults = NetworkFaults(page)
    deletes = faults.respond(CONTACT_BY_ID, "DELETE", 500)
    contacts = _login(page, temp_user)
    contacts.open_details(created_contact.phone)

    contacts.remove()
    faults.wait_for_requests(deletes)
    page.wait_for_timeout(SETTLE_MS)

    assert contacts.card_shown(created_contact.phone), "После сбоя DELETE карточка исчезла из списка"
    assert _stored(auth_api, created_contact.id), "Контакт пропал с бэкенда, хотя DELETE получил 500"


@allure.story("Good behaviour")
@allure.title("Сбой POST: контакт не создан, введённые данные остались в форме")
def test_post_failure_keeps_form_data(page: Page, temp_user, auth_api):
    faults = NetworkFaults(page)
    posts = faults.respond(CONTACTS, "POST", 500)
    contact, add_page = _add_contact_via_form(page, temp_user)
    faults.wait_for_requests(posts)
    page.wait_for_timeout(SETTLE_MS)

    assert auth_api.get_contacts_list() == [], "Контакт создан, хотя POST получил 500"
    entered = {field: getattr(contact, field) for field in PwAddContactPage.FIELD_NAMES}
    in_form = add_page.form_values()
    assert in_form == entered, f"Введённые данные потеряны: в форме {in_form}, вводили {entered}"


@allure.story("Good behaviour")
@allure.title("Пустой список: видно сообщение о пустом списке")
def test_empty_list_shows_message(page: Page, temp_user, created_contact):
    # Настоящий контакт на бэкенде есть: сообщение появляется именно из-за ответа сервера
    NetworkFaults(page).respond(CONTACTS, "GET", 200, {"contacts": []})
    contacts = _login(page, temp_user)
    contacts.check_empty_message_visible()


@allure.story("Good behaviour")
@allure.title("Медленный список: сначала индикатор загрузки, потом контакты")
def test_slow_list_shows_loading_then_contacts(page: Page, temp_user, created_contact):
    faults = NetworkFaults(page)
    held = faults.hold(CONTACTS, "GET")
    contacts = _login(page, temp_user)
    faults.wait_for_requests(held.requests)

    contacts.check_loading_visible()
    held.release()
    contacts.check_card_visible(created_contact)


# ==========================================
# НАБЛЮДЕНИЯ (требований нет, ожидание обосновано — data/observations.py)
# ==========================================
def _fail_post(page, temp_user, created_contact, faults):
    requests = faults.respond(CONTACTS, "POST", 500)
    _add_contact_via_form(page, temp_user)
    return requests


def _abort_post(page, temp_user, created_contact, faults):
    requests = faults.abort(CONTACTS, "POST")
    _add_contact_via_form(page, temp_user)
    return requests


def _fail_put(page, temp_user, created_contact, faults):
    requests = faults.respond(CONTACTS, "PUT", 500)
    contacts = _login(page, temp_user)
    contacts.open_details(created_contact.phone)
    contacts.edit_name("Changed" + created_contact.name)
    return requests


def _fail_delete(page, temp_user, created_contact, faults):
    requests = faults.respond(CONTACT_BY_ID, "DELETE", 500)
    contacts = _login(page, temp_user)
    contacts.open_details(created_contact.phone)
    contacts.remove()
    return requests


@allure.story("Observations")
@allure.title("Сбой действия виден пользователю: {action}")
@allure.tag("OBS-SILENT_FAILURE")
@observation("SILENT_FAILURE")
@pytest.mark.parametrize(
    "action, perform",
    [
        pytest.param("POST 500", _fail_post, id="post-500"),
        pytest.param("POST обрыв сети", _abort_post, id="post-abort"),
        pytest.param("PUT 500", _fail_put, id="put-500"),
        pytest.param("DELETE 500", _fail_delete, id="delete-500"),
    ],
)
def test_failure_is_shown_to_user(page: Page, temp_user, created_contact, action, perform):
    faults = NetworkFaults(page)
    feedback = PwFeedback(page)
    requests = perform(page, temp_user, created_contact, faults)
    faults.wait_for_requests(requests)

    assert feedback.error_shown(ERROR_WAIT_MS), f"{action}: пользователь не увидел сообщения об ошибке"


@allure.story("Observations")
@allure.title("Сбой PUT: форма редактирования не закрывается, введённое не теряется")
@allure.tag("OBS-EDIT_FORM_CLOSES_ON_FAILURE")
@observation("EDIT_FORM_CLOSES_ON_FAILURE")
def test_edit_form_stays_open_on_put_failure(page: Page, temp_user, created_contact):
    faults = NetworkFaults(page)
    puts = faults.respond(CONTACTS, "PUT", 500)
    contacts = _login(page, temp_user)
    contacts.open_details(created_contact.phone)
    new_name = "Changed" + created_contact.name

    contacts.edit_name(new_name)
    faults.wait_for_requests(puts)
    page.wait_for_timeout(SETTLE_MS)

    assert contacts.is_edit_form_open(), "После сбоя PUT форма редактирования закрылась"
    assert contacts.edit_name_value() == new_name, f"Введённое имя потеряно: {contacts.edit_name_value()!r}"


@allure.story("Observations")
@allure.title("Сбой списка: нет вечной загрузки")
@allure.tag("OBS-ENDLESS_LOADING")
@observation("ENDLESS_LOADING")
def test_list_failure_does_not_load_forever(page: Page, temp_user, created_contact):
    faults = NetworkFaults(page)
    gets = faults.respond(CONTACTS, "GET", 500)
    contacts = _login(page, temp_user)
    faults.wait_for_requests(gets)

    assert contacts.loading_gone_within(LOADING_LIMIT_MS), (
        f"'Loading...' не исчез за {LOADING_LIMIT_MS // 1000} с после 500 на список"
    )


@allure.story("Observations")
@allure.title("401 на список: переход на страницу входа")
@allure.tag("OBS-EXPIRED_SESSION_NO_REDIRECT")
@observation("EXPIRED_SESSION_NO_REDIRECT")
def test_expired_session_redirects_to_login(page: Page, temp_user, created_contact):
    # 403 намеренно не проверяется: для отсутствующей авторизации Swagger обещает 401
    faults = NetworkFaults(page)
    gets = faults.respond(CONTACTS, "GET", 401)
    contacts = _login(page, temp_user)  # сначала приложение переходит на /contacts — это предусловие
    faults.wait_for_requests(gets)

    assert contacts.redirected_to_login_within(LOADING_LIMIT_MS), (
        f"После 401 на список нет перехода на страницу входа, URL: {page.url}"
    )


@allure.story("Observations")
@allure.title("Двойной клик по Save: ровно один POST")
@allure.tag("OBS-DOUBLE_SUBMIT")
@observation("DOUBLE_SUBMIT")
def test_double_click_sends_one_post(page: Page, temp_user):
    faults = NetworkFaults(page)
    # Первый POST висит без ответа (как при медленной сети) — второй клик приходится на него
    held = faults.hold(CONTACTS, "POST")
    _add_contact_via_form(page, temp_user, double_click=True)
    faults.wait_for_requests(held.requests)
    page.wait_for_timeout(SECOND_CLICK_MS)

    assert len(held) == 1, f"Двойной клик по Save отправил {len(held)} запросов POST /v1/contacts"


@allure.story("Observations")
@allure.title("Обрыв сети: нет необработанных исключений страницы")
@allure.tag("OBS-UNHANDLED_NETWORK_ERROR")
@observation("UNHANDLED_NETWORK_ERROR")
def test_network_error_is_handled(page: Page, temp_user):
    faults = NetworkFaults(page)
    feedback = PwFeedback(page)
    posts = faults.abort(CONTACTS, "POST")
    _add_contact_via_form(page, temp_user)
    faults.wait_for_requests(posts)
    page.wait_for_timeout(SETTLE_MS)

    assert not feedback.page_errors, f"Необработанные исключения страницы: {feedback.page_errors}"


# ==========================================
# ИЗВЕСТНЫЙ БАГ (нарушение требования SRS)
# ==========================================
@allure.story("Double submit")
@allure.title("Двойной клик по Save: на бэкенде ровно один контакт")
@allure.tag("SRS-T45")
@known_bug("DUPLICATE_CONTACT")
def test_double_click_creates_one_contact(page: Page, temp_user, auth_api):
    faults = NetworkFaults(page)
    held = faults.hold(CONTACTS, "POST")
    contact, add_page = _add_contact_via_form(page, temp_user, double_click=True)
    faults.wait_for_requests(held.requests)
    page.wait_for_timeout(SECOND_CLICK_MS)
    held.release()  # все удержанные POST уходят на настоящий сервер

    def same_phone() -> list[dict]:
        return [c for c in auth_api.get_contacts_list() if c.get("phone") == contact.phone]

    # Даём второму запросу время дойти до бэкенда: иначе тест прошёл бы при живом дубле.
    # Ждём через Playwright (wait_until), а не eventually/time.sleep: отпущенные запросы
    # уходят в сеть, только пока тест вызывает Playwright
    add_page.wait_until(lambda: len(same_phone()) >= 2, timeout_ms=ERROR_WAIT_MS)
    assert len(same_phone()) == 1, f"Двойной клик создал {len(same_phone())} контакта с телефоном {contact.phone}"
