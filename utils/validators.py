import allure
from jsonschema import ValidationError, validate

from utils.logger import get_logger

logger = get_logger("VALIDATOR")

# Сигнатуры технических утечек в ответах с ошибкой
FORBIDDEN_PATTERNS = [
    "stack trace",
    "traceback",
    "sqlexception",
    "syntax error",
    "internal_id",
    "password_hash",
    "password=",
    "secret=",
    "/var/www/",
    "nullpointer",
]


def assert_secure_error(response, expected_status=None):
    """
    Проверяет статус-код ответа с ошибкой (если задан) и гарантирует,
    что бэкенд не "выплёвывает" технические детали (стектрейсы, SQL, пути и т.п.).
    """
    with allure.step(f"Проверка безопасности ответа с ошибкой (ожидаем статус {expected_status})"):
        if expected_status:
            assert response.status_code == expected_status, \
                f"Ожидался статус {expected_status}, но получен {response.status_code}. Тело: {response.text}"

        error_text = response.text.lower()
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in error_text, \
                f"УЯЗВИМОСТЬ: в тексте ошибки найдено критическое слово: '{pattern}'\nТело: {response.text}"

        logger.info(f"Ошибка безопасна (статус {response.status_code}, утечек нет).")


def assert_json_schema(data, schema: dict, what: str = "ответ") -> None:
    """Проверяет данные по JSON Schema.

    Падает обычным AssertionError с понятным сообщением — так же, как любой assert,
    поэтому корректно работает и со strict-xfail (raises=AssertionError).
    """
    with allure.step(f"Проверка JSON Schema: {what}"):
        try:
            validate(instance=data, schema=schema)
        except ValidationError as error:
            path = "/".join(str(p) for p in error.absolute_path) or "<корень>"
            raise AssertionError(f"{what} нарушает контракт в поле {path}: {error.message}") from None
