import os
import requests
import allure
import json
from utils.logger import get_logger

logger = get_logger("API")


class PhonebookAPI:
    BASE_URL = os.getenv("API_URL", "https://contactapp-telran-backend.herokuapp.com")

    def __init__(self):
        # 🌟 КЛЮЧЕВОЙ МОМЕНТ: Открываем единую сессию
        self.session = requests.Session()
        self.token = None


    def login(self, username, password):
        # Декоратор @allure.step здесь НЕ используем: он автоматически кладёт
        # все аргументы функции (включая password) в параметры шага,
        # и пароль виден в Allure-отчёте открытым текстом.
        # Контекстный менеджер создаёт такой же шаг, но без параметров.
        with allure.step(f"API: Авторизация пользователя {username}"):
            url = f"{self.BASE_URL}/v1/user/login/usernamepassword"
            logger.info(f"POST {url} [User: {username}]")

            payload = {"username": username, "password": password}
            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                self.token = response.json().get("token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("Авторизация успешна (токен добавлен в заголовки сессии)")
            else:
                logger.error(f"Ошибка авторизации: {response.status_code} - {response.text}")

            return response

    def register(self, username, password):
        # Причина отказа от @allure.step — та же, что и в login()
        with allure.step(f"API: Регистрация нового пользователя {username}"):
            url = f"{self.BASE_URL}/v1/user/registration/usernamepassword"
            logger.info(f"POST {url} [Регистрация: {username}]")

            payload = {"username": username, "password": password}
            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                self.token = response.json().get("token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("Регистрация успешна (токен добавлен в заголовки сессии)")
            else:
                logger.error(f"Ошибка регистрации: {response.status_code} - {response.text}")

            return response

    @allure.step("API: Создание контакта")
    def add_contact(self, contact_payload):
        url = f"{self.BASE_URL}/v1/contacts"
        phone = contact_payload.get('phone', 'UNKNOWN')
        logger.info(f"POST {url} [Контакт: {phone}]")

        # Нам больше не нужно передавать headers! Сессия сделает всё сама.
        response = self.session.post(url, json=contact_payload)

        # Красиво цепляем тело запроса в Allure
        allure.attach(json.dumps(contact_payload, indent=4), name="Payload",
                      attachment_type=allure.attachment_type.JSON)
        return response

    @allure.step("API: Получение списка контактов")
    def get_contacts(self):
        url = f"{self.BASE_URL}/v1/contacts"
        logger.info(f"GET {url} [Запрос всех контактов]")
        return self.session.get(url)

    @allure.step("API: Обновление контакта")
    def update_contact(self, contact_payload):
        url = f"{self.BASE_URL}/v1/contacts"
        logger.info(f"PUT {url} [Обновление контакта ID: {contact_payload.get('id')}]")

        response = self.session.put(url, json=contact_payload)

        allure.attach(json.dumps(contact_payload, indent=4), name="Payload",
                      attachment_type=allure.attachment_type.JSON)
        return response

    @allure.step("API: Удаление контакта {contact_id}")
    def delete_contact(self, contact_id):
        url = f"{self.BASE_URL}/v1/contacts/{contact_id}"
        logger.info(f"DELETE {url} [ID: {contact_id}]")
        return self.session.delete(url)

    @allure.step("API: Массовое удаление всех контактов")
    def clear_contacts(self):
        url = f"{self.BASE_URL}/v1/contacts/clear"
        logger.info(f"DELETE {url} [Массовая очистка]")
        return self.session.delete(url)