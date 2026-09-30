# 🛠 Шпаргалка по командам проекта (Cheatsheet)

## 🏃‍♂️ Запуск тестов локально (Без Docker)
Перед локальным запуском убедись, что в `.env` стоит `USE_SELENOID=false`.

**Запуск всех тестов параллельно (в 4 потока) с генерацией отчета:**
`pytest tests/ -n 4 --clean-alluredir --alluredir=allure-results`

**Запуск конкретного файла (например, только логин):**
`pytest tests/test_login.py --clean-alluredir --alluredir=allure-results`

**Запуск Playwright тестов в видимом (Headed) режиме для дебага:**
`pytest tests/test_playwright_login.py -s --headed`

---

## 📊 Работа с Allure Report
**Сгенерировать и открыть красивый HTML-отчет в браузере:**
`allure serve allure-results`

**Сгенерировать отчет в статичную папку (без открытия браузера):**
`allure generate allure-results -o allure-report --clean`

---

## 🐳 Запуск через Docker Compose (Изолированная среда)
Перед запуском убедись, что в `.env` стоит `USE_SELENOID=true`.

**Полный запуск (Сборка образа -> Запуск Селеноида -> Прогон тестов -> Выход):**
`docker compose up --build --exit-code-from qa-framework`

**Остановка и удаление контейнеров (после завершения работы):**
`docker compose down`

---

## 🧹 Очистка и обслуживание Docker (Если что-то зависло)
**Убить все активные контейнеры проекта и удалить сети:**
`docker compose down -v`

**Удалить зависшие "сироты" (orphans) контейнеры:**
`docker compose down --remove-orphans`

**ГЛОБАЛЬНАЯ ОЧИСТКА ДОКЕРА (Осторожно! Удалит все неиспользуемые контейнеры, образы и кэш на ПК):**
`docker system prune -a --volumes`

**Точечно обновить образ браузера для Селеноида (если вышла новая версия Chrome):**
`docker pull selenoid/chrome:128.0`

---

## 🐙 Полезные команды Git
**Заставить Git "забыть" файл, но оставить его на жестком диске (например, `.env` или `logs/`):**
`git rm --cached <путь_к_файлу>`

**Обновить файл зависимостей проекта:**
`pip freeze > requirements.txt`