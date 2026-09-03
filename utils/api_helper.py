import requests
import allure
import json
import copy


def make_api_request(method, url, **kwargs):
    """
    Умная обертка над requests.
    Автоматически логирует все детали запроса и ответа в Allure-отчет,
    маскируя при этом чувствительные данные (пароли и токены).
    """
    with allure.step(f"API Request: {method} {url}"):

        # Выполняем сам запрос
        response = requests.request(method, url, **kwargs)

        # 1. Прикрепляем тело запроса (С МАСКИРОВКОЙ ПАРОЛЯ)
        if "json" in kwargs:
            # Делаем глубокую копию, чтобы не испортить реальный запрос
            payload_to_log = copy.deepcopy(kwargs["json"])

            # Если в теле запроса есть пароль - прячем его
            if isinstance(payload_to_log, dict) and "password" in payload_to_log:
                payload_to_log["password"] = "*** HIDDEN FOR SECURITY ***"

            allure.attach(
                json.dumps(payload_to_log, indent=4, ensure_ascii=False),
                name="📥 Request Body (Что мы отправили)",
                attachment_type=allure.attachment_type.JSON
            )

        # 2. Пытаемся красиво отформатировать ответ сервера (С МАСКИРОВКОЙ ТОКЕНА)
        try:
            response_dict = response.json()

            # Если сервер вернул нам токен - прячем его
            if isinstance(response_dict, dict) and "token" in response_dict:
                response_dict["token"] = "*** HIDDEN FOR SECURITY ***"

            response_body = json.dumps(response_dict, indent=4, ensure_ascii=False)
            attach_type = allure.attachment_type.JSON
        except ValueError:
            # Если сервер вернул текст или HTML
            response_body = response.text
            attach_type = allure.attachment_type.TEXT

        # 3. Прикрепляем ответ сервера к отчету
        allure.attach(
            f"Status Code: {response.status_code}\n\n{response_body}",
            name="📤 Response (Что ответил сервер)",
            attachment_type=attach_type
        )

        return response