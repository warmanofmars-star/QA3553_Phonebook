import csv
import os


def load_contact_data_from_csv():
    """Читает негативные сценарии из CSV файла и возвращает их списком"""

    # 1. Получаем точный путь к нашему CSV файлу, где бы мы ни запускали тест
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'negative_contacts.csv')

    data = []

    # 2. Открываем файл
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        # Пропускаем первую строку (заголовки столбцов: name, last_name и т.д.)
        next(reader)

        # 3. Читаем остальные строки и добавляем их в список
        for row in reader:
            data.append(tuple(row))

    return data