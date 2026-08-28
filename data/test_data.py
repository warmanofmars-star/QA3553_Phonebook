import csv
import os
import pytest


def load_contact_data_from_csv():
    """Читает негативные сценарии из CSV файла и возвращает их списком"""

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'negative_contacts.csv')

    data = []

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Пропускаем заголовки

        for row in reader:
            # Распаковываем строку на переменные для удобства
            name, last_name, phone, email, address, description, expected_error = row

            # ИЗВЕСТНЫЙ БАГ: система не выдает Alert, если Имя, Фамилия, Email или Адрес пустые.
            if name == "" or last_name == "" or email == "" or address == "":

                # Оборачиваем проблемные данные в pytest.param и вешаем маркер xfail
                marked_row = pytest.param(*row, marks=pytest.mark.xfail(
                    reason="BUG: Alert doesn't appear for empty fields"))
                data.append(marked_row)

            else:
                # Если бага нет, добавляем данные как обычно
                data.append(tuple(row))

    return data