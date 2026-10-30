"""
Логирование проекта.

Модули получают логгер так:

    from utils.logger import get_logger
    logger = get_logger("API")
    logger.info("POST /v1/contacts -> 200")

Здесь НЕ настраиваются ни обработчики, ни форматы, ни файлы — этим занимается pytest
(секция логирования в pytest.ini и хук pytest_configure в conftest.py).
Логгер лишь передаёт записи наверх, к корневому логгеру, где их уже ждёт pytest:

  * для упавших тестов показывает их в разделе "Captured log";
  * прикладывает к каждому тесту в Allure как вложение "log";
  * пишет в файл logs/pytest.log (при xdist — отдельный файл на каждый воркер);
  * при запуске с -o log_cli=true выводит их в консоль в реальном времени.

Раньше здесь был самописный логгер со своими обработчиками. Он печатал в stdout
(в Allure каждое сообщение лежало дважды: в "log" и в "stdout") и полностью
отключал файловые логи при параллельном запуске — то есть во всех прогонах в CI и Docker.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Логгер с коротким именем компонента: API, UI, STEP, DRIVER..."""
    return logging.getLogger(name)
