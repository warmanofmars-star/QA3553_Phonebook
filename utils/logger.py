import logging
import os
import sys


class ColoredFormatter(logging.Formatter):
    """Кастомный класс для раскрашивания логов в терминале с помощью ANSI-кодов"""

    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMAT_TEMPLATE = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"

    FORMATS = {
        logging.DEBUG: FORMAT_TEMPLATE,
        logging.INFO: GREEN + FORMAT_TEMPLATE + RESET,
        logging.WARNING: YELLOW + FORMAT_TEMPLATE + RESET,
        logging.ERROR: RED + FORMAT_TEMPLATE + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT_TEMPLATE + RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def get_logger(name="PhonebookQA"):
    logger = logging.getLogger(name)

    # ИСПРАВЛЕНИЕ ЗДЕСЬ: проверяем именно список handlers нашего логгера
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 1. ЗАЩИТА ОТ PYTEST: Запрещаем Pytest перехватывать и прятать наши логи (тумблер)
    logger.propagate = True

    # 2. ФАЙЛОВАЯ СИСТЕМА: Создаем папку logs, если ее еще нет
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 3. ОБРАБОТЧИК ДЛЯ КОНСОЛИ (Цветной)
    # Явно указываем sys.stdout, чтобы логи пробивались через настройки Pytest
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())

    # 4. ОБРАБОТЧИК ДЛЯ ФАЙЛА (Чистый текст, без иероглифов цвета)
    file_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Записываем в файл logs/test.log
    file_handler = logging.FileHandler("logs/test.log", encoding='utf-8')
    file_handler.setFormatter(file_formatter)

    # Подключаем оба обработчика
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger