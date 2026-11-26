# 🛠 Шпаргалка по командам проекта Phonebook (Cheatsheet)


## 🏃‍♂️ Запуск тестов локально (Без Docker)
Перед локальным запуском убедись, что в `.env` стоит `USE_GRID=false`
(или переопредели на текущий сеанс PowerShell: `$env:USE_GRID="false"`).

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

## 🐳 Запуск через Docker Compose (Selenium Grid 4)
Значение `USE_GRID` в `.env` здесь не важно: docker-compose.yml сам передаёт контейнеру `USE_GRID=true`.
Образы хаба и узлов браузеров compose скачивает сам при первом запуске.

Браузер задаётся **двумя** переменными с одинаковым значением (`chrome`, `firefox` или `edge`):
`COMPOSE_PROFILES` — какие узлы браузеров запустить, `BROWSER` — в каком браузере идут тесты.

**Полный запуск (Сборка образа -> Запуск Grid -> Прогон тестов -> Выход):**
- В PowerShell: `$env:COMPOSE_PROFILES="chrome"; $env:BROWSER="chrome"; docker compose up --build --exit-code-from qa-framework`
- В Bash: `COMPOSE_PROFILES=chrome BROWSER=chrome docker compose up --build --exit-code-from qa-framework`

**Запуск только части тестов (маркеры передаются через `PYTEST_ADDOPTS`):**
- В PowerShell: `$env:COMPOSE_PROFILES="firefox"; $env:BROWSER="firefox"; $env:PYTEST_ADDOPTS='-m "smoke"'; docker compose up --build --exit-code-from qa-framework`
- В Bash: `COMPOSE_PROFILES=firefox BROWSER=firefox PYTEST_ADDOPTS='-m "smoke"' docker compose up --build --exit-code-from qa-framework`

**Grid UI (какие узлы подключены, какие сессии идут) — пока стенд запущен:**
`http://localhost:4444/ui/` *(косая черта в конце обязательна: без неё интерфейс не загружается)*

**Другой порт хоста для Grid (если 4444 занят):**
- В PowerShell: `$env:GRID_HOST_PORT="4446"; $env:COMPOSE_PROFILES="chrome"; $env:BROWSER="chrome"; docker compose up --build --exit-code-from qa-framework`
- В Bash: `GRID_HOST_PORT=4446 COMPOSE_PROFILES=chrome BROWSER=chrome docker compose up --build --exit-code-from qa-framework`
*(Grid UI тогда — `http://localhost:4446/ui/`. По умолчанию 4444; сборки Jenkins используют 4445 — см. Jenkinsfile, — поэтому локальный стенд и сборка Jenkins больше не роняют друг друга. Тестам внутри compose порт хоста не важен: они ходят к `selenium-hub:4444`. При локальном запуске тестов с хоста через Grid (`USE_GRID=true`) поменяй и `GRID_URL` в `.env`)*

**Только API- и Playwright-тесты, без Selenium Grid (как job «Tests (api)» в GitHub Actions):**
- В Bash: `PYTEST_ADDOPTS='-m "api or playwright"' docker compose run --rm --no-deps --build qa-framework`

**Остановка и удаление контейнеров тестового стенда (после завершения работы):**
`docker compose down -v --remove-orphans`
*(Узлы браузеров входят в профили: чтобы `down` их увидел, нужен тот же `COMPOSE_PROFILES`, что при запуске)*
*(Безопасно для Jenkins: он в отдельном проекте `phonebook-jenkins-server` и в «сироты» больше не попадает)*

---

## 🧹 Очистка и обслуживание Docker
**Удалить зависшие "сироты" (orphans) контейнеры и тома:**
`docker compose down -v --remove-orphans`

**Очистить диск от безымянных (dangling) слоев образов:**
`docker image prune -f`

---

## 🧹 Качество кода (ruff, pre-commit, gitleaks)
**Установка инструментов разработки и хуков (один раз после клонирования):**
`pip install -r requirements.txt -r requirements-dev.txt`
`pre-commit install`

**Проверить весь проект теми же хуками, что срабатывают перед коммитом:**
`pre-commit run --all-files`

**Только линтер / только форматирование:**
`ruff check .` (с автоисправлением: `ruff check --fix .`)
`ruff format .`

**Проверить ВСЮ историю git на секреты (вывод без самих секретов):**
`gitleaks git --redact` *(если gitleaks установлен отдельно; pre-commit проверяет только новые изменения, CI — только новые коммиты)*

---

## 📦 Обновить зависимости
Версии меняются только в `requirements.in` (тесты) и `requirements-dev.in` (ruff, pre-commit, PyYAML,
check-jsonschema). Плановые обновления раз в месяц приносит Dependabot — раздел ниже.
`requirements.txt` и `requirements-dev.txt` — lock-файлы: всё дерево пакетов, генерирует pip-compile, руками
не правятся. Пересборка — только в контейнере с образом из строки `FROM` в `Dockerfile`: pip-compile
разрешает зависимости под текущие ОС и Python, на Windows в lock попали бы пакеты вроде colorama.

**Сначала — образ из строки `FROM` в `Dockerfile` (PowerShell, из корня проекта; один раз на сессию):**
`$img = (Select-String -Path Dockerfile -Pattern '^FROM\s+(\S+)' | Select-Object -First 1).Matches[0].Groups[1].Value; $img`
*(тег не вписан в команды руками: версия Python живёт только в `FROM`, поменяли там — команды подхватят сами)*

**Пересобрать lock-файлы:**
`docker run --rm -v "${PWD}:/src" -w /src $img bash ci/lock_requirements.sh`

**Поднять один пакет до последней версии, допустимой исходником:**
`docker run --rm -v "${PWD}:/src" -w /src $img bash ci/lock_requirements.sh --upgrade-package requests`

**Проверить, что lock-файлы соответствуют исходникам (то же делает job Lint):**
`docker run --rm -v "${PWD}:/src" -w /src $img bash ci/lock_requirements.sh --check`
Код 0 — пины совпадают, 1 — расходятся (печатается, что добавится, исчезнет, изменится). Сравниваются пины
«имя==версия», а не текст: шапка и пометки `# via` зависят от версии pip-tools, а Dependabot пересобирает
lock-файлы своей.

**Затем поставить обновлённое в venv:**
`pip install -r requirements.txt -r requirements-dev.txt`

---

## 📦 Dependabot: обновления зависимостей (`.github/dependabot.yml`)

**Что приходит.** Один PR в месяц на все экосистемы сразу: pip (`requirements*.in` и lock-файлы),
pre-commit (rev внешних хуков; local-хуки бот пропускает), GitHub Actions, Docker (`Dockerfile`),
Docker Compose (образы Selenium Grid). Заголовок — `build(deps): …`. Одна группа и раз в месяц — потому что
каждый PR запускает полный CI, а каждый прогон навсегда регистрирует пользователей на общем бэкенде
(порядка 260 за прогон — оценка по сбору тестов, не замер). Выдержка — 14 дней: версия моложе двух недель
в PR не попадает. Для образа `python` — только патчи (3.14.x): переход на новую минорную Python — отдельное
решение, не PR бота. Образ Jenkins (`Dockerfile.jenkins`) бот не обновляет совсем: CI Jenkins не собирает
и не запускает, зелёный PR о нём ничего бы не проверил.
Образы `selenium/*` — только теги по версии Grid (`4.x.y-<дата>`): в `ignore` всё `>= 5` — теги по версии
браузера (например `141.0-<дата>`) и Selenium 5. Иначе бот разводит узлы и хаб по разным схемам тегов,
а откат браузера тесты не ловят. Поэтому теги ещё проверяет `ci/check_selenium_images.py` (хук pre-commit
и шаг `lint`): все образы `selenium/*` в `docker-compose*.yml` — на одном теге вида `4.x.y-<дата>`.
**Мажор Selenium — вручную:** правило в `dependabot.yml` и шаблон тега в проверке меняются вместе.
Security updates (если они включены в настройках репозитория) — отдельные PR: вне расписания, без
выдержки и без группировки с обычными обновлениями.

**Как ревьюить PR бота** (ревьюит и сливает пользователь):
1. **Полный CI зелёный до слияния** — все job'ы, включая `lint`: актуальность lock-файлов по пинам, теги
   Selenium, конфиги по схеме. Dependabot пересобирает lock-файлы своей версией pip-tools — шапка и «# via»
   могут отличаться, проверка сравнивает только пины.
2. Список обновлений в описании PR — ожидаемые ли пакеты и версии.
3. Даты выпуска (PyPI, Docker Hub, релизы на GitHub): **ловушка групп** — в группе выдержка считается
   на группу, а не на каждый пакет, и PR может подтянуть пакет моложе 14 дней. Такой пакет — не сливать,
   пока ему не исполнится две недели (или исключить его, см. ниже).
4. Мажорные версии — читать changelog: ломающие изменения тесты могут и не задеть.

**PR красный.** Чаще всего — lock-файлы (`lint`) или несовместимость версий (`pip check` при сборке
образа). Починить на ветке PR: `git fetch origin`, `git switch <ветка PR>`, пересобрать lock-файлы
в контейнере (команда — «Обновить зависимости» выше), закоммитить, push. После чужого коммита бот
перестаёт сам перебазировать PR. Комментарии в PR:
- `@dependabot rebase` — перебазировать PR;
- `@dependabot recreate` — по документации пересоздаёт PR заново, **затирая** все правки в нём.
  **На групповом PR из нескольких экосистем не работает** (проверено в IlCarro): задание запускается для
  одной экосистемы и откладывает работу — «Detected existing pull request … Deferring creation of a new
  pull request», ветка не меняется.
Чтобы бот мог перезаписывать ветку поверх твоих коммитов, в их сообщение добавляют `[dependabot skip]`.

**PR красный из-за проекта, а не из-за файлов бота** (новая версия требует правки `Dockerfile`, кода,
конфигов) — чинить **отдельным PR в main**, в ветку бота не коммитить: после чужого коммита Dependabot
перестаёт её вести. Когда фикс в main — комментарий `@dependabot rebase` в PR бота и снова полный CI.
Пример: playwright 1.63 → 1.65 — Node в драйвере стал требовать `libatomic.so.1`, сборка образа падала
на `playwright install --with-deps` (exit 127); фикс — `libatomic1` в `Dockerfile` отдельным PR.

**Групповой PR надо поправить** — не ждать `recreate` и не закрывать PR: поправить ветку PR руками,
дождаться зелёного CI и слить. **Закрытие группового PR ничего не игнорирует:** в следующий раз бот
предложит те же обновления.

**Журнал бота** (что сделало задание и почему): Insights → Dependency graph → Dependabot → Recent update
jobs → view logs → View logs.

**Исключить зависимость.** Основной способ — `ignore` в `.github/dependabot.yml` (по задаче): видно
в git, почему пакет не обновляется. Быстрый — комментарий в групповом PR (условие хранится в настройках
репозитория, а не в файле):
- `@dependabot ignore ИМЯ` — не обновлять пакет; `@dependabot ignore ИМЯ major version` (или `minor`,
  `patch`) — не обновлять эту часть версии;
- `@dependabot show ИМЯ ignore conditions` — какие условия записаны; `@dependabot unignore ИМЯ` — снять.

**Версии вне Dependabot** — бот их не видит или намеренно пропускает, обновлять вручную:
- `PIP_TOOLS_VERSION` в `ci/lock_requirements.sh` — переменная shell, а не манифест;
- `allure-commandline` в `.github/workflows/tests.yml` — ставится `npm install -g` без `package.json`;
- минорная версия Python в `Dockerfile` — намеренно в `ignore` (патчи бот предлагает);
- образ Jenkins в `Dockerfile.jenkins` — намеренно в `ignore`: правка `FROM`, пересборка
  (`docker compose -f docker-compose.jenkins.yml up -d --build`) и проверка локально, только вперёд.

Документация GitHub: «Dependabot options reference», «Configuring multi-ecosystem updates»,
«Dependabot pull request comment commands».

---

## 🐙 Полезные команды Git
**Заставить Git "забыть" файл, но оставить его на диске (например, `.env` или `logs/`):**
`git rm --cached <путь_к_файлу>`

**Цикл работы над задачей (ветка → PR → слияние):**
`git switch main && git pull` → `git switch -c <тип>/<название>` → коммиты →
`git push -u origin <ветка>` → PR на GitHub → после слияния:
`git switch main && git pull && git branch -d <ветка> && git fetch --prune`
