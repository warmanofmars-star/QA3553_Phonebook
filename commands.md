# 🛠 Шпаргалка по командам проекта Phonebook (Cheatsheet)


## 🏃‍♂️ Запуск тестов локально (Без Docker)
Перед локальным запуском убедись, что в `.env` стоит `USE_SELENOID=false`
(или переопредели на текущий сеанс PowerShell: `$env:USE_SELENOID="false"`).

**Запуск всех тестов (UI + API) параллельно в 4 потока с генерацией отчета:**
`pytest -n 4 --clean-alluredir --alluredir=allure-results`

**Запуск с выбором конкретного браузера (`chrome`, `firefox`, `edge` — Edge только локально, в Selenoid его нет):**
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

## 🤖 Jenkins в Docker
**Запуск (первый раз или после изменения Dockerfile.jenkins):**
`docker compose -f docker-compose.jenkins.yml up -d --build`

**Остановка (настройки и сборки сохраняются в томе `jenkins_home`):**
`docker compose -f docker-compose.jenkins.yml down`
*(Том `jenkins_home` объявлен внешним: compose не удаляет его даже с `-v`. На новой машине перед первым запуском создай его один раз: `docker volume create jenkins_home`)*

**Логи Jenkins (например, начальный пароль администратора):**
`docker logs jenkins-master`

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
Значение `USE_SELENOID` в `.env` здесь не важно: docker-compose.yml сам передаёт контейнеру `USE_SELENOID=true`.

**Полный запуск (Сборка образа -> Запуск Selenoid -> Прогон тестов -> Выход):**
`docker compose up --build --exit-code-from qa-framework`

**Запуск только части тестов (маркеры передаются через `PYTEST_ADDOPTS`):**
- В PowerShell: `$env:PYTEST_ADDOPTS='-m "smoke"'; docker compose up --build --exit-code-from qa-framework`
- В Bash: `PYTEST_ADDOPTS='-m "smoke"' docker compose up --build --exit-code-from qa-framework`

**Запуск в изолированном Firefox через Docker Compose:**
- В PowerShell (Windows):
  `$env:BROWSER="firefox"; docker compose up --build --exit-code-from qa-framework`
- В Bash / Linux:
  `BROWSER=firefox docker compose up --build --exit-code-from qa-framework`

**Остановка и удаление контейнеров тестового стенда (после завершения работы):**
`docker compose down -v --remove-orphans`
*(Безопасно для Jenkins: он в отдельном проекте `phonebook-jenkins-server` и в «сироты» больше не попадает)*

---

## 🧹 Очистка и обслуживание Docker
**Удалить зависшие "сироты" (orphans) контейнеры и тома:**
`docker compose down -v --remove-orphans`

**Очистить диск от безымянных (dangling) слоев образов:**
`docker image prune -f`

**Скачать образы VNC-браузеров для Selenoid (Selenoid сам их не скачивает):**
*(Это последние существующие версии: проект Selenoid больше не развивается)*
`docker pull selenoid/vnc_chrome:128.0`
`docker pull selenoid/vnc_firefox:125.0`
`docker pull selenoid/video-recorder:latest-release`

---

## 🧹 Качество кода (ruff, pre-commit, gitleaks)
**Установка инструментов разработки и хуков (один раз после клонирования):**
`pip install -r requirements-dev.txt`
`pre-commit install`

**Проверить весь проект теми же хуками, что срабатывают перед коммитом:**
`pre-commit run --all-files`

**Только линтер / только форматирование:**
`ruff check .` (с автоисправлением: `ruff check --fix .`)
`ruff format .`

**Проверить ВСЮ историю git на секреты (вывод без самих секретов):**
`gitleaks git --redact` *(если gitleaks установлен отдельно; pre-commit проверяет только новые изменения)*

---

## 🐙 Полезные команды Git
**Заставить Git "забыть" файл, но оставить его на диске (например, `.env` или `logs/`):**
`git rm --cached <путь_к_файлу>`

**Цикл работы над задачей (ветка → PR → слияние):**
`git switch main && git pull` → `git switch -c <тип>/<название>` → коммиты →
`git push -u origin <ветка>` → PR на GitHub → после слияния:
`git switch main && git pull && git branch -d <ветка> && git fetch --prune`
