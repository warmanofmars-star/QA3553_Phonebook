# 📖 Phonebook Hybrid Test Automation Framework

[![UI Tests in Docker](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

Robust, production-ready hybrid test automation framework for the "Phonebook" web application, featuring a fully containerized **Infrastructure as Code (IaC)** approach, cross-browser CI/CD matrix execution, and enterprise-grade API security & contract testing.

This project demonstrates a **Senior-level approach** to QA automation, combining classic UI testing, deep API validation, remote browser execution via Selenoid, advanced network mocking, and modern container orchestration.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **UI Frameworks:** Selenium WebDriver 4+ (Chrome, Firefox, Edge), Playwright (Sync API)
* **API & Contract Testing:** Requests, `jsonschema`
* **Containerization & Orchestration:** Docker, Docker Compose, Selenoid (with video-recorder)
* **Test Runner:** Pytest (with `pytest-xdist` for parallel execution)
* **Design Pattern:** Page Object Model (POM)
* **Data Modeling & Generation:** Python `dataclasses`, Faker & UUID, CSV (DDT)
* **Reporting:** Allure Report (with embedded videos and secure data masking)
* **CI/CD:** GitHub Actions, Jenkins (Parameterized Declarative Pipelines), Ngrok (Webhook Tunneling)
* **Notifications:** Telegram Bot API
* **Security:** `python-dotenv` for managing sensitive credentials

## 🚀 Key Architectural Features

* **Self-Hosted CI/CD Lifecycle:** Fully autonomous Jenkins pipeline with dynamic parameters (Browser selection), strict Allure environment injection, automated workspace cleanup, dangling Docker image pruning, and GitHub Webhook integration via Ngrok.
* **Advanced Allure Matrix Deduplication:** Features a custom Python-based post-processor injected into GitHub Actions. It dynamically mutates `testCaseId` and `historyId` in raw JSON results to merge parallel cross-browser execution arrays (Chrome & Firefox) into a single unified Allure dashboard without test collapsing.
* **Total Data Isolation (Sandbox Pattern):** UI, API, and Playwright tests rely on dynamic API fixtures (`temp_user`) to instantly provision isolated user accounts on the fly, eliminating race conditions during high-concurrency `pytest-xdist` runs.
* **Strict API Contract Validation (JSON Schema):** All positive API responses are validated against strict JSON Schemas enforcing `additionalProperties: False` to catch undocumented fields, type mismatches, and contract violations.
* **Data-Driven Negative Mutations (DDT):** Utilizes inline `lambda` mutations with `@pytest.mark.parametrize` (backed by a custom `pytest_make_parametrize_id` hook for `xdist` compatibility) to dynamically corrupt valid payloads on the fly.
* **API Security & Vulnerability Auditing:** Dedicated security suite covering Broken Object Level Authorization (BOLA / IDOR), JWT authentication token tampering, `DELETE` idempotency, HTTP method restrictions (`405`), and media type validation (`415`).
* **Global Data Leak Scanner:** Custom `assert_secure_error()` validator automatically scans all negative API responses for sensitive backend exposures (`stack trace`, `sql`, `exception`, `password`, internal paths).
* **Defect Documentation via XFAIL:** Known backend contract violations and security flaws are strictly documented in code using `@pytest.mark.xfail(reason=...)` without polluting CI/CD pipeline stability.
* **OOP Payload Serialization (Dataclasses):** Test data models (`Contact`, `User`) encapsulate their own API mapping logic via `.to_api_payload()`, eliminating hardcoded dictionaries across test suites.
* **API Connection Pooling:** Utilizes `requests.Session()` for backend interactions, reusing TCP connections and automatically managing Bearer tokens.
* **Network Interception & Mocking:** Leverages Playwright's `page.route()` to intercept frontend requests and mock backend API responses, ensuring ultra-fast, isolated testing of UI rendering logic.
* **Cross-Browser CI/CD Matrix & Docker IaC:** Configured GitHub Actions matrix strategy to dynamically spawn parallel test suites in Google Chrome and Mozilla Firefox inside isolated Docker Compose / Selenoid containers.
* **Universal Video Attachment:** Every Selenium session is recorded via FFmpeg/Selenoid, while Playwright tests utilize the native recording engine. All `.mp4` files are automatically attached to the Allure report upon teardown.
* **Security & Context-Aware Logging:** Sensitive data (passwords, tokens) are strictly masked (`********`) across console outputs, test IDs, and Allure reports. Features a thread-safe custom logger that adapts to `pytest-xdist` workers.
* **Test Categorization (Pytest Markers):** Implements a granular tagging system (`smoke`, `regression`, `api`, `ui`, `hybrid`, `security`, `playwright`) with dynamic marker injection directly from the GitHub Actions UI.

## ⚙️ Setup & Installation

### 1. Clone and Setup
```bash
git clone https://github.com/warmanofmars-star/QA3553_Phonebook.git
cd QA3553_Phonebook
python -m venv .venv
source .venv/Scripts/activate  # For Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Environment Variables (.env)
Create a `.env` file in the root directory and add your credentials:
```env
HEADLESS_MODE=false
USE_SELENOID=false
ENABLE_CONSOLE_LOGS=true
ALLOW_MASS_DELETE=false
USER_EMAIL=your_valid_email@gmail.com
USER_PASSWORD=Your_Valid_Password123$
BASE_URL=https://telranedu.web.app
API_URL=https://contactapp-telran-backend.herokuapp.com
```

## 🏃‍♂️ How to Run Tests

**Run all tests in the isolated Docker container (Recommended):**
```bash
docker compose up --build --exit-code-from qa-framework
```

**Run locally via Pytest (parallel execution & specific browser):**
```bash
pytest -n 4 --browser_name=firefox --clean-alluredir --alluredir=allure-results
```

**Run specific test categories (using Pytest markers):**
```bash
pytest -m "api" -n 2 -v           # Run all API tests in parallel
pytest -m "api and security" -v   # Run API security & BOLA checks
pytest -m "smoke and ui" -n 2     # Run only UI smoke tests
pytest -m "hybrid" -v             # Run hybrid (API Setup -> UI Action) tests
```

**Generate and view Allure Report locally:**
```bash
allure serve allure-results
```

## 🛠 Utility Scripts

The project includes standalone utility scripts for database and documentation management:
```bash
# Export all contacts of the current user into a formatted JSON file (data/exported_contacts.json)
python export_contacts.py

# Regenerate README.md dynamically
python make_readme.py
```

## 🏗 Project Structure
```text
QA3553_Phonebook/
├── .github/workflows/    # CI/CD pipeline configuration with Matrix (tests.yml)
├── api/                  # API Client (Requests Session) for backend interactions
├── api_tests/            # Pure API test suites (CRUD, Payload mutations, Auth, Security, BOLA)
├── data/                 # Test data generators (Faker, UUID, CSV loader)
├── models/               # Data classes with API payload serialization (Contact, User)
├── pages/                # Page Object classes (Selenium BasePage & Playwright PwBasePage)
├── schemas/              # Strict JSON Schema contracts for API validation
├── selenoid/             # Selenoid configuration (browsers.json)
├── tests/                # Hybrid, UI (Selenium), and Playwright test suites
├── utils/                # Custom logger, WebDriver listener, Error & Security validators
├── logs/                 # Auto-rotating, thread-safe local log files
├── commands.md           # Quick CLI cheatsheet for local, Docker, and marker runs
├── conftest.py           # Pytest fixtures, Selenoid remote connection, video attachment hooks
├── pytest.ini            # Pytest configuration and marker registration
├── Dockerfile            # Container definition for the test framework
├── docker-compose.yml    # Infrastructure orchestration (Selenoid + Framework + Network + Volumes)
├── export_contacts.py    # Standalone utility script to export DB via API
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---
*Author: Maksim Vinogradov*
