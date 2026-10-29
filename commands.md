# 🛠 Шпаргалка по командам проекта Phonebook (Cheatsheet)


## 🏃‍♂️ Запуск тестов локально (Без Docker)
Перед локальным запуском убедись, что в `.env` стоит `USE_SELENOID=false`.

**Запуск всех тестов (UI + API) параллельно в 4 потока с генерацией отчета:**
`pytest -n 4 --clean-alluredir --alluredir=allure-results`

**Запуск с выбором конкретного браузера (`chrome`, `firefox`, `edge`):**
`pytest -n 4 --browser_name=firefox --clean-alluredir --alluredir=allure-results`

**Быстрый прогон только API-слоя (без браузеров):**
`pytest -m "api" -v`

**Запуск проверок безопасности и BOLA:**
`pytest -m "security" -v`

**Запуск по связке маркеров (логическое И / ИЛИ / НЕ):**
`pytest -m "api and security" -v`
`pytest -m "smoke and ui" -n 2`
`pytest -m "hybrid" -v`
`pytest -m "playwright" -v`

**Запуск Playwright тестов в видимом (Headed) режиме для дебага:**
`pytest tests/test_playwright_login.py -s --headed`

---

## 🚇 Ngrok & Jenkins Webhooks (Локальный CI/CD)
**Авторизация в Ngrok (единоразово в консоли Windows):**
`ngrok config add-authtoken <ТВОЙ_ТОКЕН>`

**Запуск туннеля для Jenkins (проброс порта 8080 в интернет):**
`ngrok http 8080`
*(Скопируй HTTPS ссылку из консоли, добавь `/github-webhook/` и вставь в настройки репозитория GitHub -> Webhooks)*

---

## 📊 Работа с Allure Report
**Сгенерировать и открыть красивый HTML-отчет в браузере:**
`allure serve allure-results`

**Сгенерировать отчет в статичную папку (без открытия браузера):**
`allure generate allure-results -o allure-report --clean`

---

## 🐳 Запуск через Docker Compose (Изолированная среда)
Перед запуском убедись, что в `.env` стоит `USE_SELENOID=true`.

**Полный запуск (Сборка образа -> Запуск Selenoid -> Прогон тестов -> Выход):**
`docker compose up --build --exit-code-from qa-framework`

**Запуск в изолированном Firefox через Docker Compose:**
- В PowerShell (Windows):
  `$env:BROWSER="firefox"; docker compose up --build --exit-code-from qa-framework`
- В Bash / Linux:
  `BROWSER=firefox docker compose up --build --exit-code-from qa-framework`

**Остановка и удаление контейнеров (после завершения работы):**
`docker compose down -v --remove-orphans`

---

## 🧹 Очистка и обслуживание Docker
**Удалить зависшие "сироты" (orphans) контейнеры и тома:**
`docker compose down -v --remove-orphans`

**Очистить диск от безымянных (dangling) слоев образов:**
`docker image prune -f`

**Точечно обновить образы VNC-браузеров для Selenoid:**
`docker pull selenoid/vnc_chrome:128.0`
`docker pull selenoid/vnc_firefox:125.0`
`docker pull selenoid/video-recorder:latest-release`

---

## 🐙 Полезные команды Git и документации
**Сгенерировать актуальный README.md из скрипта:**
`python make_readme.py`

**Заставить Git "забыть" файл, но оставить его на диске (например, `.env` или `logs/`):**
`git rm --cached <путь_к_файлу>`

**Обновить файл зависимостей проекта:**
`pip freeze > requirements.txt`