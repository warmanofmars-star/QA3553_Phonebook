import csv
from pathlib import Path

import pytest

from data.known_bugs import known_bug
from models.contact import Contact

DATA_DIR = Path(__file__).resolve().parent


def load_negative_contacts() -> list:
    """Читает негативные сценарии создания контакта из negative_contacts.csv.

    Колонки CSV:
      test_case      — номер кейса из STD (TC-0013 ... TC-0017)
      scenario       — короткое имя сценария, вместе с test_case образует id теста
      name ... description — данные формы
      expected_error — текст ошибки ПО ТРЕБОВАНИЮ (SRS F5–F9), а не по факту приложения
      known_bug      — ключ из data/known_bugs.py, если сценарий упирается в известный дефект

    Раньше загрузчик сам решал, какие строки xfail, по признаку "какое поле пустое".
    Теперь это явно записано в данных: открыл CSV — и видно, какой баг ловит строка.
    """
    params = []
    with open(DATA_DIR / "negative_contacts.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            contact = Contact(
                name=row["name"],
                last_name=row["last_name"],
                phone=row["phone"],
                email=row["email"],
                address=row["address"],
                description=row["description"],
            )
            marks = [known_bug(row["known_bug"])] if row["known_bug"] else []
            params.append(pytest.param(
                contact, row["expected_error"], row["test_case"],
                id=f'{row["test_case"]}-{row["scenario"]}',  # читаемый id: TC-0013-empty-name
                marks=marks,
            ))
    return params
