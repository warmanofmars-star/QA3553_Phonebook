# 📖 Phonebook Hybrid Test Automation Framework

[![UI Tests in Docker](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

Robust, production-ready hybrid test automation framework for the "Phonebook" web application, featuring a fully containerized **Infrastructure as Code (IaC)** approach and cross-browser CI/CD matrix execution.

This project demonstrates a **Senior-level approach** to QA automation, combining classic UI testing, API integration, remote browser execution via Selenoid, and modern container orchestration.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **UI Frameworks:** Selenium WebDriver 4+, Playwright (Sync API)
* **API Testing:** Requests, jsonschema
* **Containerization & Orchestration:** Docker, Docker Compose, Selenoid (with video-recorder)
* **Test Runner:** Pytest (with `pytest-xdist` for parallel execution)
* **Design Pattern:** Page Object Model (POM)
* **Test Data:** Faker (dynamic generation of names, phones, emails)
* **Reporting:** Allure Report (with embedded videos and secure data masking)
* **CI/CD:** GitHub Actions (Containerized pipeline with Build Matrix)
* **Notifications:** Telegram Bot API
* **Security:** `python-dotenv` for managing sensitive credentials

## 🚀 Key Architectural Features

* **Advanced Allure Matrix Deduplication:** Features a custom Python-based post-processor injected into GitHub Actions. It dynamically mutates `testCaseId` and `historyId` in raw JSON results to merge parallel cross-browser execution arrays (Chrome & Firefox) into a single unified Allure dashboard without test collapsing.
* **Total Data Isolation (Sandbox Pattern):** UI tests rely on dynamic API fixtures (`temp_user`) to instantly provision and tear down fully isolated user accounts on the fly, eliminating data collisions during high-concurrency `pytest-xdist` runs.
* **Network Interception & Mocking:** Leverages Playwright to intercept frontend requests and mock backend API responses, ensuring ultra-fast, completely isolated testing of UI components.
* **Cross-Browser CI/CD Matrix:** Configured GitHub Actions matrix strategy to dynamically spawn parallel test suites in Google Chrome and Mozilla Firefox inside isolated Docker containers.
* **Dockerized Infrastructure (IaC):** The entire test environment—including the framework, Selenoid hub, browser instances, and video recording modules—is orchestrated via Docker Compose.
* **Automatic Video Attachment:** Every test execution session is recorded via FFmpeg/Selenoid, and the resulting `.mp4` files are automatically attached to the Allure report upon teardown.
* **Thread-Safe Custom Logging:** Proprietary logging utility with dual-stream outputs, ANSI-colored console logs, and individual log files per Process ID (`PID`).
* **Test Categorization (Pytest Markers):** Implements a robust tagging system (`smoke`, `regression`, `api`, `ui`, `security`, `playwright`) for granular execution control. Includes dynamic marker injection directly from the GitHub Actions UI.
* **Strict API Contract & Security Validation:** Enforces deep backend validation using `jsonschema` (checking structure, types, and formats) and `lambda`-based payload mutations for negative testing. Includes dedicated security validators to detect data leaks, broken object-level authorization (BOLA), and idempotency issues.

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
ALLOW_MASS_DELETE=false
USER_EMAIL=your_valid_email@gmail.com
USER_PASSWORD=Your_Valid_Password123$
BASE_URL=https://telranedu.web.app
API_URL=https://contactapp-telran-backend.herokuapp.com
```

## 🏃‍♂️ How to Run Tests

**Run tests in the isolated Docker container (Recommended):**
```bash
docker compose up --build --exit-code-from qa-framework
```

**Run locally via Pytest (parallel execution & specific browser):**
```bash
pytest tests/ -n auto --browser_name=firefox --clean-alluredir --alluredir=allure-results
```

**Run specific test categories (using Pytest markers):**
```bash
pytest -m "smoke and ui" -n 2  # Run only UI smoke tests in 2 threads
pytest -m "api or security"    # Run API and security tests
```

**Generate and view Allure Report locally:**
```bash
allure serve allure-results
```

## 🛠 Utility Scripts

The project includes standalone utility scripts for database and artifact management:
```bash
# Export all contacts of the current user into a formatted JSON file (data/exported_contacts.json)
python export_contacts.py
```

## 🏗 Project Structure
```text
QA3553_Phonebook/
├── .github/workflows/    # CI/CD pipeline configuration with Matrix (tests.yml)
├── api_tests/            # Pure API test suites (Payload validation, Auth, Security, BOLA)
├── data/                 # Test data generators (Faker, DataClasses)
├── models/               # Data models (Contact, User)
├── pages/                # Page Object classes (Selenium BasePage & Playwright PwBasePage)
├── schemas/              # JSON Schema contracts for strict API validation
├── selenoid/             # Selenoid configuration (browsers.json)
├── tests/                # Hybrid and UI Test suites
├── utils/                # Custom logger, WebDriver listener, Error validators, API helpers
├── logs/                 # Auto-rotating, thread-safe local log files
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
