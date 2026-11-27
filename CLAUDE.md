# CLAUDE.md — правила проекта для Claude Code

Учебный фреймворк автотестов (UI + API) для веб-приложения Phonebook: Python 3.14, pytest,
Selenium, Playwright, Allure, Docker, GitHub Actions, Jenkins. Подробности — в README.md.

## Безопасность (обязательно)

- **Никогда не читай и не выводи `.env`** — там реальные учётные данные. Нужен список настроек —
  смотри `.env.example` и `config.py`. Изменения в `.env` пользователь вносит сам.
- **Поиск по содержимому — только `git grep`** (или с явным исключением `.env`). Почему: запрет
  `Read` в `.claude/settings.json` не действует на команды Bash, и рекурсивный `grep -r`/`rg` по корню
  прочитает `.env`. А `git grep` ищет только по отслеживаемым файлам, `.env` в git нет.
- **Не делай `git push`, не создавай PR и не сливай ветки** — это делает пользователь вручную.
  Коммитить в текущую рабочую ветку можно.
- Не коммить секреты, токены, пароли, файлы из `.gitignore`. Перед коммитом — `pre-commit run --all-files`.

## Команды

```bash
pytest -n 4 --alluredir=allure-results       # весь набор локально (USE_GRID=false в .env)
pytest -m api                                # только API-тесты
pytest --collect-only -q                     # сколько тестов собирается
pre-commit run --all-files                   # ruff, проверки файлов, схемы конфигов GitHub, теги Selenium, gitleaks
ruff check . && ruff format --check .        # только линтер и форматирование
```

Docker (Selenium Grid 4): браузер задаётся двумя переменными с одинаковым значением.

```bash
COMPOSE_PROFILES=chrome BROWSER=chrome docker compose up --build --exit-code-from qa-framework
```

Маркеры передаются через `PYTEST_ADDOPTS`, например `PYTEST_ADDOPTS='-m "smoke and ui"'`.
Маркеры: `smoke`, `regression`, `api`, `ui`, `hybrid`, `security`, `playwright`.

## Соглашения проекта

- **Комментарии, docstring'и, сообщения в assert'ах и логах — на русском.** Комментарий объясняет,
  ПОЧЕМУ код такой, а не пересказывает его.
- **Коммиты — Conventional Commits** (`feat`, `fix`, `refactor`, `test`, `ci`, `build`, `chore`, `docs`),
  заголовок на английском, без даты.
- **Переменные окружения читаются только в `config.py`.** Остальной код импортирует `settings`.
- **Ожидаемый результат теста берётся из требований** (SRS, Swagger, STD), а не из текущего поведения
  приложения.
- **Известные баги — только через реестр `data/known_bugs.py`** и маркер `@known_bug("KEY")`
  (строгий xfail, `raises=AssertionError`). Новый баг добавляется в реестр со ссылкой на требование.
  Без ссылки на требование — это не баг, и xfail ставить нельзя.
- **Предусловия проверяются через `require()`** (`utils/preconditions.py`), а не через `assert`:
  иначе сломанное окружение спрячется за известным багом.
- **Проверки безопасности отдельно от проверок контракта:** безопасность — по состоянию данных,
  точный код ответа — отдельным тестом.
- **UI-тесты:** предусловия через API (фикстуры `create_contact`, `created_contact`, `temp_user`),
  действие через UI, результат — через API. Негативные асинхронные проверки — через `eventually()`.
- **Сбои бэкенда в Playwright-тестах (`utils/network_faults.py`) — только через фикстуру
  `network_faults`**, не `NetworkFaults(page)`: на teardown она проверяет, что каждый установленный
  сбой перехватил хотя бы один запрос (иначе ERROR — его не спрячет строгий xfail).
- **`respond()` без тела — только для статусов из `ERROR_BODIES`;** для остальных (200, 404, 502...)
  тело передаётся явно, иначе `ValueError`.
- **Page Objects:** публичные методы — действия пользователя с декоратором `@step`; локаторы и
  ожидания — приватные (`_click`, `_is_visible`...). В тестах нет локаторов и `WebDriverWait`.
- **Каждому тесту — свой временный пользователь** (`temp_user`). Постоянный аккаунт из `.env`
  тестам не нужен.
- **Зависимости правятся только в `requirements.in` / `requirements-dev.in`.** `requirements.txt`
  и `requirements-dev.txt` — lock-файлы (всё дерево, pip-compile): руками не правятся, генерирует их
  `ci/lock_requirements.sh` — только в контейнере с образом из `FROM` в `Dockerfile` (команда —
  `commands.md`, «Обновить зависимости»). Установка — `pip install -r requirements.txt -r requirements-dev.txt`.
  Актуальность проверяет job Lint (`ci/lock_requirements.sh --check`) — по пинам «имя==версия»,
  а не по тексту. Без `--upgrade` и без хэшей.
- **У каждого инструмента — одно место версии.** ruff — `requirements-dev.in` (хуки ruff
  в `.pre-commit-config.yaml` — `repo: local`, `language: system`; job Lint ставит ruff из lock-файла);
  gitleaks — `rev` в `.pre-commit-config.yaml` (job Secrets читает оттуда тег образа; rev не вида
  `vX.Y.Z` — красный шаг); Python для Docker — точный тег в `FROM` в `Dockerfile` (команды пересборки
  lock-файлов в `commands.md` читают его оттуда). Дубли версий не заводи. Коммить из активированного
  `.venv` — иначе хуки ruff не найдут ruff.
- **Dependabot** (`.github/dependabot.yml`): одна группа на все экосистемы, раз в месяц, выдержка 14 дней,
  Python — только патчи, Jenkins и Selenium 5 — вручную. **PR Dependabot ревьюит и сливает пользователь —
  агент их не сливает.** `dependabot.yml` меняется только по задаче. Как ревьюить и версии вне Dependabot —
  `commands.md`, раздел про Dependabot.
- **Конфиги GitHub проверяются по JSON-схемам**, встроенным в check-jsonschema (версия — только
  `requirements-dev.in`, сеть не нужна): хуки `check-dependabot` и `check-github-workflows`
  (`repo: local`, `language: system`) и те же шаги job Lint. Образы `selenium/*` в `docker-compose*.yml`
  — на одном теге Grid 4 `4.x.y-<дата>` (`ci/check_selenium_images.py`: хук и шаг job Lint); мажор
  Selenium меняется вручную вместе с правилом `ignore` в `dependabot.yml`.
- Совместимость кода — Python 3.12+ (`target-version` в `pyproject.toml`), запуск — на 3.14.
  Локальный venv — `py -3.14 -m venv .venv` (Windows) или `python3.14 -m venv .venv`: просто `python`
  может оказаться другой версией.
- **В Git Bash не активируй `.venv` через `source .venv/Scripts/activate`.** Если сессия запущена
  из терминала с уже активированным venv (PyCharm/PowerShell), в окружении есть `_OLD_VIRTUAL_PATH`
  в формате Windows (`C:\...;C:\...`); `activate` восстанавливает из неё PATH, и пропадают
  `grep`, `tail`, `uname`. Вместо этого — `.venv/Scripts/python.exe -m ...` или
  `PATH="$PWD/.venv/Scripts:$PATH"` (так же для коммита, чтобы хуки нашли ruff).
- **Требования проекта — в `docs/requirements/`** (SRS в PDF, лежит только локально,
  в git не попадает). Ожидаемые результаты тестов берутся оттуда; номера требований
  (T1–T86, F1–F16) используются в тегах тестов, например `@allure.tag("SRS-T41")`.

## Как работать над задачей

- Работай в той ветке, на которой ты запущен; если это `main` — остановись и спроси.
  Исключение: если задача явно в режиме «только чтение», на `main` работать можно, ничего не меняя.
- **Обычный запуск pytest удаляет `logs/*.log` прошлого прогона** (`pytest_configure`
  в `conftest.py`). Нужные логи сохрани до запуска. `--collect-only` и `ci/coverage_matrix.py`
  (и его хук pre-commit) логи не трогают.
- **Матрица покрытия:** после изменения тегов тестов, `data/known_bugs.py`, `data/observations.py`
  или `docs/requirements_index.yml` — `python ci/coverage_matrix.py`, и `docs/coverage.md` в тот же
  коммит (хук pre-commit `coverage-matrix` и job Lint проверят `--check`). Справочник проверяется
  закрыто: неизвестный ключ или флаг не bool — ошибка; новый ключ — сначала в константы генератора.
- **Упавшие тесты и XPASS не «чини» навешиванием xfail и не ослабляй проверки.** Собери данные
  (тест, браузер, текст ошибки, воспроизводится ли повторно) и сообщи — решение принимает пользователь.
- Инфраструктурные проблемы (Docker, Grid, зависимости) можно чинить самостоятельно, но каждое
  изменение объясни в отчёте.
- В конце задачи — короткий отчёт: что сделано, результаты прогонов (passed / xfailed / failed /
  XPASS), все изменения сверх задачи, открытые вопросы.
