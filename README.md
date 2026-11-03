# Phonebook — Test Automation Framework

[![Tests](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml)
**Live Allure report:** [warmanofmars-star.github.io/QA3553_Phonebook](https://warmanofmars-star.github.io/QA3553_Phonebook/)

UI and API test automation for the [Phonebook](https://telranedu.web.app) training web application:
**129 tests** (85 API, 44 UI) in Python + pytest, running locally, in Docker with Selenium Grid 4
(Chrome, Firefox, Edge), in GitHub Actions and in a self-hosted Jenkins.

This is a learning project built during a QA automation course. It was later refactored
step by step after a code review against enterprise practices; the reasoning behind the main
decisions is documented below and in the code comments.

---

## What is tested

The application under test is a contact book: registration, login and CRUD for contacts,
with a React frontend and a REST backend.

| Area | Examples |
|---|---|
| **API** | contacts CRUD, JSON Schema validation, negative payloads, auth tokens |
| **API security** | BOLA (access to another user's contacts), mass assignment, BFLA, error message leaks |
| **UI** | registration and login, adding / editing / deleting contacts, form validation |
| **Hybrid** | preconditions via API, action via UI, result verified via API |
| **Playwright** | login, network interception (backend response mocking) |

Expected behaviour comes from the project documentation, not from the current behaviour of the app:
the **SRS** (requirements T1–T86, F1–F16), the **Swagger** contract and the manual test design (**STD**,
test cases TC-0001…TC-0036). UI tests are tagged with their STD case id in the Allure report.

## Known bugs

The application is no longer maintained, so found defects will never be fixed. Tests that hit them
are marked as expected failures — but only through a single registry, [`data/known_bugs.py`](data/known_bugs.py),
where every defect is linked to the requirement it violates:

| Key | Requirement | Actual behaviour |
|---|---|---|
| `DUPLICATE_CONTACT` | SRS T32, T45, T70, T83; Swagger 409 | Duplicate email / phone is saved |
| `EMAIL_NOT_REQUIRED` | SRS T26–T27, T64–T65 | Contact with an empty email is saved |
| `PHONE_NOT_REQUIRED` | SRS T38–T39 | Contact without a phone is saved |
| `EDIT_DESCRIPTION_BROKEN` | STD TC-00026, TC-00027 | Editing the description in UI saves `[object Undefined]` |
| `CUSTOMER_CAN_CLEAR_ALL` | SRS, section 2 | A regular user can delete all contacts (BFLA) |
| `WRONG_CONTENT_TYPE_500` | HTTP semantics | `text/plain` body crashes the server with 500 |
| `NO_AUTH_403` | Swagger 401 | Missing `Authorization` header returns 403 |
| `NOT_FOUND_400` | Swagger 404 | Missing or foreign contact returns 400 |
| `PASSWORD_NO_MAX_LENGTH` | SRS T15 | Password longer than 15 characters is accepted; there is no upper limit |
| `PASSWORD_NON_LATIN_ALLOWED` | SRS T10 | Non-Latin letters in the password are accepted |
| `EMAIL_NON_LATIN_ALLOWED` | SRS T6, T31 | Non-Latin letters in the email are accepted (registration and contacts) |
| `TYPE_COERCION` | Swagger `type: string` | Boolean in `name` is silently accepted |
| `NO_ERROR_ON_EMPTY_FIELD` | SRS F5, F6, F9 | Empty required field shows no error message |
| `USER_EXISTS_WORDING` | SRS F3 | Error text differs from the requirement |
| `EMAIL_ERROR_WORDING` | SRS F7 | Error text differs from the requirement |

All known bugs reproduce identically in Chrome, Firefox and Edge, so they are defects of the application,
not of a particular browser.

How the registry protects the test results:

- **Strict xfail.** If a "known bug" test suddenly passes, the run fails with `XPASS` — the behaviour
  changed and the test must be reviewed.
- **Only assertion failures are expected.** `raises=AssertionError`: a timeout, a network error or a bug
  in the test code is reported as a normal failure, not hidden behind a known bug.
- **Preconditions are not assertions.** Setup steps use `require()` ([`utils/preconditions.py`](utils/preconditions.py)),
  so a broken environment is never reported as an expected defect.
- **Security checks are separate from contract checks.** For example, the BOLA test verifies that the other
  user's data is intact and has no xfail; the exact status code is checked by a separate contract test.

## Key design decisions

- **A fresh user for every test.** The `temp_user` fixture registers a new user via API, so tests are
  isolated from each other and from any real data, and run safely in parallel (`pytest-xdist`).
  No permanent account credentials are needed to run the suite.
- **API for preconditions and verification, UI for the action.** The `create_contact` / `created_contact`
  fixtures prepare data via API; UI tests then check the saved state via API instead of trusting what the
  page shows. This is how the `EDIT_DESCRIPTION_BROKEN` bug was found.
- **Negative async checks wait for the bad thing to happen.** `eventually()` ([`utils/waits.py`](utils/waits.py))
  polls the backend for a few seconds — a check right after a click would pass while the bug is still there.
- **Readable reports.** Page Object actions are Allure steps with human-readable names (`@step`);
  API calls attach the request and the response, with passwords and tokens masked.
- **One place for configuration.** Environment variables are read only in [`config.py`](config.py);
  everything else imports `settings`.

## Project structure

```text
api/            API client: single request() entry point, timeouts, masked Allure attachments
api_tests/      API, contract and security tests
tests/          Selenium UI tests and Playwright tests
pages/          Page Objects (public user actions; waits and locators are private)
drivers/        WebDriver factory: local browsers or Selenium Grid
data/           test data generators, negative CSV data, known bugs registry
models/         Contact and User dataclasses
schemas/        JSON Schemas for API responses
utils/          logging, Allure steps, waits, validators, preconditions
ci/             script that merges cross-browser Allure results in GitHub Actions
```

## Running the tests

### Locally

Requires **Python 3.14** (the code itself is compatible with 3.12+).

```bash
git clone https://github.com/warmanofmars-star/QA3553_Phonebook.git
cd QA3553_Phonebook
python -m venv .venv
.venv\Scripts\activate             # Windows; on Linux / macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
cp .env.example .env               # Windows: copy .env.example .env
```

Set `USE_GRID=false` in `.env` to run browsers locally, then:

```bash
pytest -n 4 --alluredir=allure-results       # the whole suite in 4 parallel workers
pytest -m api                                # API tests only
pytest -m "smoke and ui" --browser_name=firefox
allure serve allure-results                  # open the report
```

Markers: `smoke`, `regression`, `api`, `ui`, `hybrid`, `security`, `playwright`.
All settings are described in [`.env.example`](.env.example) and [`config.py`](config.py).

### In Docker (Selenium Grid 4)

The browser is selected by two variables with the same value — `chrome`, `firefox` or `edge`:
`COMPOSE_PROFILES` starts the browser nodes, `BROWSER` tells the tests which browser to use.

```bash
COMPOSE_PROFILES=chrome BROWSER=chrome docker compose up --build --exit-code-from qa-framework
COMPOSE_PROFILES=edge BROWSER=edge PYTEST_ADDOPTS='-m "smoke"' docker compose up --build --exit-code-from qa-framework
```

Selenium tests run on Selenium Grid nodes (a hub and two nodes of the selected browser). Each node records
a video of its sessions, and the video is attached to the Allure report. Compose pulls the Grid images itself.
While the stack is running, the Grid UI is available at `http://localhost:4444/ui/` (the trailing slash is required).
The stack previously used Selenoid; it was replaced because the project is discontinued.
More commands: [`commands.md`](commands.md).

## CI

**GitHub Actions** ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) runs on every push to `main`
and on every pull request:

- a linter job (ruff);
- a secrets job (gitleaks) that scans only the new commits of the push or pull request;
- tests in Chrome, Firefox and Edge in parallel (matrix), each in Docker Compose with Selenium Grid;
- one Allure report for all browsers with trend history, published to GitHub Pages from `main`
  (for pull requests it is available as a build artifact);
- a Telegram notification with the result and test counts.

Failed tests fail the pipeline; the report is generated anyway.

**Jenkins** ([`Jenkinsfile`](Jenkinsfile)) runs in a local Docker container
([`docker-compose.jenkins.yml`](docker-compose.jenkins.yml)) and is triggered by a GitHub webhook through
an ngrok tunnel. Parameters: browser and pytest markers. Failed tests mark the build `UNSTABLE`,
infrastructure errors mark it `FAILURE`; the Allure plugin keeps the trend history.

## Code quality

- **ruff** — linter and formatter, configured in [`pyproject.toml`](pyproject.toml); also checked in CI.
- **pre-commit** ([`.pre-commit-config.yaml`](.pre-commit-config.yaml)) — runs ruff, basic file checks and
  **gitleaks** before every commit. Besides the built-in gitleaks rules, a custom rule in
  [`.gitleaks.toml`](.gitleaks.toml) catches `.env`-style passwords, which the built-in rules do not detect.
  The same gitleaks version and config run in CI on new commits, where the check cannot be skipped.

```bash
pre-commit install            # once after cloning
pre-commit run --all-files    # check the whole project manually
```

## Known limitations

- **The Jenkins setup is for local learning only.** The test stack itself no longer needs the Docker
  socket, but Jenkins still runs `docker compose` through the host Docker socket: its container runs
  as root with access to it (which effectively means root on the host), builds run on the controller itself,
  and Jenkins is exposed through ngrok. In a production setup builds would run on ephemeral agents,
  the grid would be a shared long-running service, and Jenkins would not be publicly accessible.
- **No `data-testid` attributes in the app.** Locators rely on stable prefixes of CSS Modules class names,
  e.g. `[class^='contact-item_card__']`; a frontend rebuild with different class prefixes would break them.
- **Tests depend on an external training environment.** The frontend and the backend (on Heroku) are not
  part of this repository; if they are down, the tests fail.
- **Playwright coverage is minimal:** two tests demonstrating the approach, including network mocking.
  The main UI suite uses Selenium.
- **Videos are available only in Docker.** Grid nodes write them to a Docker volume that a local run
  cannot access.
- **Cosmetic issue in Allure:** every fixture shows an extra `<fixture>::<lambda>` teardown step with
  the *Unknown* status. It is an incompatibility between pytest 9 (which registers an internal finalizer
  for every fixture) and allure-pytest 2.16; test results are not affected.

## License

[Apache License 2.0](LICENSE)
