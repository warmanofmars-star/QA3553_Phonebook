"""
Декоратор шагов для Page Objects.

Почему не стандартный @allure.step:
  * он кладёт ВСЕ аргументы метода в параметры шага. Для страниц это пароли
    (login), локаторы-кортежи и целые объекты Contact — шум или утечка;
  * он ничего не пишет в лог, поэтому шаги в Allure и строки в логе жили отдельно,
    и тесты дублировали каждое действие вручную: logger.info("ШАГ 1: ...").

@step делает шаг в Allure БЕЗ параметров и одновременно пишет его название в лог.
В названии можно подставлять аргументы метода по имени, включая их атрибуты:

    @step("Открыть карточку контакта {phone}")
    def open_details(self, phone): ...

    @step("Войти как {email}")              # password в название не подставляем —
    def login(self, email, password): ...   # и в параметры шага он тоже не попадёт
"""

import functools
import inspect

import allure

from utils.logger import get_logger

logger = get_logger("STEP")


def step(title: str):
    def decorator(func):
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            values = {name: value for name, value in bound.arguments.items() if name != "self"}
            step_title = title.format(**values)

            logger.info(step_title)
            with allure.step(step_title):
                return func(*args, **kwargs)

        return wrapper

    return decorator
