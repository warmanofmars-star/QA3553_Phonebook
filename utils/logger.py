import logging
import os
import sys
import glob
from datetime import datetime


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


def clean_old_logs(log_dir="logs", keep_last=5):
    """Удаляет старые файлы логов, оставляя только N самых свежих."""
    if not os.path.exists(log_dir):
        return

    # Ищем все .log файлы и сортируем их по времени изменения (самые старые в начале)
    files = glob.glob(os.path.join(log_dir, "*.log"))
    files.sort(key=os.path.getmtime)

    # Удаляем файлы, пока их количество не станет равным keep_last
    while len(files) > keep_last:
        oldest_file = files.pop(0)
        try:
            os.remove(oldest_file)
        except OSError:
            pass


def get_logger(name="PhonebookQA"):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 1. Запускаем "пылесос" перед созданием нового файла
    clean_old_logs("logs", keep_last=5)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())

    # 2. Генерируем уникальное имя файла с точным временем запуска
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"logs/run_{current_time}.log"

    file_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 3. Подключаем обычный FileHandler (файл создастся с нуля)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger