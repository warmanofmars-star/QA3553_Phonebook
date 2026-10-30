"""
API-клиент для бэкенда Phonebook.

Устройство:
  * request()           — единая точка ВСЕХ HTTP-запросов: адрес, таймаут,
                          логирование и вложение в Allure делаются только здесь.
  * login / register    — авторизация; токен автоматически добавляется в сессию.
  * add_contact и т.п.  — бизнес-методы: каждый = один понятный шаг в Allure.
  * find_contact_id и т.п. — хелперы для предусловий в тестах.

Шаги Allure создаются через `with allure.step(...)`, а не декоратором @allure.step:
декоратор кладёт ВСЕ аргументы функции в параметры шага — так в отчёт утекали
пароли, а payload контакта дублировался (и параметром, и вложением).
"""

import json

import allure
import requests

from config import settings
from utils.logger import get_logger

logger = get_logger("API")

# Ключи, значения которых никогда не показываем в отчётах и логах
SENSITIVE_KEYS = {"password", "token"}

# Ограничение размера вложения: ответ со списком из сотен контактов
# не должен превращать Allure-отчёт в простыню
MAX_ATTACHMENT_CHARS = 3000


def _mask_sensitive(data):
    """Рекурсивно заменяет значения чувствительных ключей на звёздочки.

    Работает с вложенными словарями и списками; исходные данные не меняет.
    """
    if isinstance(data, dict):
        return {
            key: "********" if key.lower() in SENSITIVE_KEYS else _mask_sensitive(value)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_mask_sensitive(item) for item in data]
    return data


def _format_body(body) -> str:
    """Превращает тело запроса/ответа в читаемый текст с маскировкой секретов."""
    if body is None or body == "":
        return "<пусто>"
    if isinstance(body, (dict, list)):
        text = json.dumps(_mask_sensitive(body), indent=2, ensure_ascii=False)
    else:
        text = str(body)
    if len(text) > MAX_ATTACHMENT_CHARS:
        text = text[:MAX_ATTACHMENT_CHARS] + f"\n... (обрезано, всего {len(text)} символов)"
    return text


class PhonebookAPI:
    # Таймаут (подключение, чтение) в секундах. Без него requests ждёт ответа
    # БЕСКОНЕЧНО, и зависший бэкенд подвешивает весь CI.
    DEFAULT_TIMEOUT = (5, 30)

    def __init__(self, base_url: str = settings.api_url):
        # Session переиспользует TCP-соединения и хранит общие заголовки (токен)
        self.session = requests.Session()
        self.base_url = base_url
        self.token: str | None = None

    # ==========================================
    # НИЗКИЙ УРОВЕНЬ: единая точка запросов
    # ==========================================
    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Отправляет HTTP-запрос к API.

        Публичный метод: им пользуются бизнес-методы ниже, и его же вызывают
        негативные тесты, когда нужен "неправильный" запрос (чужой метод,
        кривой Content-Type и т.п.).

        :param method: HTTP-метод: "GET", "POST", "PUT", "DELETE"...
        :param path:   путь от корня API, например "/v1/contacts"
        :param kwargs: всё, что принимает requests (json=, data=, headers=, timeout=...)
        """
        kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)
        url = f"{self.base_url}{path}"

        response = self.session.request(method, url, **kwargs)

        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        # Ошибочные ответы пишем уровнем WARNING — их проще найти в логе
        log = logger.info if response.ok else logger.warning
        log(f"{method} {path} -> {response.status_code} ({elapsed_ms} ms)")

        self._attach_exchange(method, url, kwargs, response, elapsed_ms)
        return response

    @staticmethod
    def _attach_exchange(method, url, request_kwargs, response, elapsed_ms) -> None:
        """Прикрепляет к текущему шагу Allure запрос и ответ одним вложением."""
        request_body = request_kwargs.get("json", request_kwargs.get("data"))
        try:
            response_body = response.json()
        except ValueError:  # ответ не JSON (пустой, HTML-страница ошибки и т.п.)
            response_body = response.text

        report = (
            f"{method} {url}\n"
            f"Статус: {response.status_code} ({elapsed_ms} ms)\n\n"
            f"--- Тело запроса ---\n{_format_body(request_body)}\n\n"
            f"--- Тело ответа ---\n{_format_body(response_body)}\n"
        )
        allure.attach(
            report,
            name=f"{method} {response.status_code}",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ==========================================
    # АВТОРИЗАЦИЯ
    # ==========================================
    def login(self, username: str, password: str) -> requests.Response:
        with allure.step(f"API: Авторизация пользователя {username}"):
            return self._authenticate("/v1/user/login/usernamepassword", username, password)

    def register(self, username: str, password: str) -> requests.Response:
        with allure.step(f"API: Регистрация нового пользователя {username}"):
            return self._authenticate("/v1/user/registration/usernamepassword", username, password)

    def _authenticate(self, path: str, username: str, password: str) -> requests.Response:
        """Общая логика login/register: запрос + сохранение токена при успехе."""
        response = self.request("POST", path, json={"username": username, "password": password})
        if response.status_code == 200:
            self._set_token(response.json().get("token"))
        return response

    def _set_token(self, token: str) -> None:
        """Сохраняет токен: дальше сессия сама подставляет его в каждый запрос."""
        self.token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        logger.info("Токен добавлен в заголовки сессии")

    # ==========================================
    # КОНТАКТЫ (CRUD)
    # ==========================================
    def add_contact(self, contact_payload: dict) -> requests.Response:
        phone = contact_payload.get("phone", "без телефона")
        with allure.step(f"API: Создание контакта (телефон {phone})"):
            return self.request("POST", "/v1/contacts", json=contact_payload)

    def get_contacts(self) -> requests.Response:
        with allure.step("API: Получение списка контактов"):
            return self.request("GET", "/v1/contacts")

    def update_contact(self, contact_payload: dict) -> requests.Response:
        with allure.step(f"API: Обновление контакта {contact_payload.get('id')}"):
            return self.request("PUT", "/v1/contacts", json=contact_payload)

    def delete_contact(self, contact_id: str) -> requests.Response:
        with allure.step(f"API: Удаление контакта {contact_id}"):
            return self.request("DELETE", f"/v1/contacts/{contact_id}")

    def clear_contacts(self) -> requests.Response:
        with allure.step("API: Массовое удаление всех контактов"):
            return self.request("DELETE", "/v1/contacts/clear")

    # ==========================================
    # ХЕЛПЕРЫ ДЛЯ ПРЕДУСЛОВИЙ И ПРОВЕРОК
    # ==========================================
    # Возвращают готовые данные вместо Response и сами проверяют статус.
    # Если что-то пошло не так, тест падает с понятным сообщением
    # ещё на этапе подготовки, а не на непонятном KeyError дальше.

    def get_contacts_list(self) -> list[dict]:
        """Список контактов текущего пользователя."""
        response = self.get_contacts()
        assert response.status_code == 200, (
            f"Не удалось получить список контактов: {response.status_code} {response.text}"
        )
        return response.json().get("contacts", [])

    def get_contact_ids(self) -> list[str]:
        """id всех контактов текущего пользователя."""
        return [contact.get("id") for contact in self.get_contacts_list()]

    def find_contact_id(self, phone: str) -> str:
        """id контакта по телефону (телефоны в тестах уникальны благодаря генератору)."""
        contact_id = next(
            (c.get("id") for c in self.get_contacts_list() if c.get("phone") == phone),
            None,
        )
        assert contact_id is not None, f"Контакт с телефоном {phone} не найден у пользователя"
        return contact_id
