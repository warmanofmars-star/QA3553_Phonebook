# Берем официальный образ Python 3.12
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузеры для Playwright
RUN playwright install --with-deps chromium

# Копируем весь проект внутрь контейнера
COPY . .

# Команда по умолчанию для запуска тестов в 4 потока
CMD ["pytest", "tests/", "-n", "4", "--clean-alluredir", "--alluredir=allure-results"]