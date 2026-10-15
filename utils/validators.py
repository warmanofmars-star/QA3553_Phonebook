import allure
from utils.logger import get_logger

logger = get_logger("VALIDATOR")


def assert_secure_error(response, expected_status=None):
    """
    Глобальный валидатор ошибок (Проверки 11-13 из статьи).
    Проверяет статус-код и гарантирует, что бэкенд не 'выплевывает' секретные данные.
    """
    with allure.step(f"Проверка безопасности ответа с ошибкой"):
        if expected_status:
            assert response.status_code == expected_status, \
                f"Ожидался статус {expected_status}, но получен {response.status_code}. Тело: {response.text}"

        error_text = response.text.lower()

        # Список слов, которых НИКОГДА не должно быть в ответах API для клиента
        forbidden_patterns = [
            "stack trace", "traceback", "exception",
            "sql", "syntax error", "internal_id",
            "password", "secret", "/var/www/", "nullpointer"
        ]

        for pattern in forbidden_patterns:
            assert pattern not in error_text, \
                f"УЯЗВИМОСТЬ (Блок 3)! В тексте ошибки найдено критическое слово: '{pattern}'\nТело: {response.text}"

        logger.info(f"Ошибка безопасна (статус {response.status_code}, утечек нет).")