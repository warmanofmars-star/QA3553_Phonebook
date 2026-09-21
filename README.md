# 📖 Phonebook Hybrid Test Automation Framework

[![Phonebook UI Tests](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

Robust, production-ready hybrid test automation framework for the "Phonebook" web application.
This project demonstrates a **Senior-level approach** to QA automation, combining classic UI testing, API integration, and modern tools to ensure fast, stable, and secure test execution.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **UI Frameworks:** Selenium WebDriver 4+, Playwright (Sync API)
* **API Testing:** Requests
* **Test Runner:** Pytest (with `pytest-xdist` for parallel execution)
* **Design Pattern:** Page Object Model (POM)
* **Test Data:** Faker (dynamic generation of names, phones, emails)
* **Reporting:** Allure Report (with secure data masking)
* **CI/CD:** GitHub Actions (Automated runs with Headless browser execution)
* **Notifications:** Telegram Bot API
* **Security:** `python-dotenv` for managing sensitive credentials

## 🚀 Key Architectural Features

* **Hybrid Testing Approach (API + UI):** Tests use API calls to set up preconditions (e.g., creating a contact) and teardown data, drastically reducing UI test execution time and ensuring test isolation.
* **Dual Framework Support:** Implemented primarily using **Selenium** with an integrated **Playwright** module to demonstrate modern tool capabilities and auto-waiting concepts.
* **Smart Browser Cascading:** The framework automatically detects the environment. It runs headless Google Chrome in CI/CD (GitHub Actions) for consistency, but gracefully falls back to Microsoft Edge for local execution if Chrome is unavailable.
* **Security & Log Masking:** Sensitive data (passwords, auth tokens) are strictly masked (********) in all console outputs, test logs, and Allure step reports.
* **Thread-Safe Custom Logging:** Features a proprietary logging utility with dual-stream outputs. It provides real-time, ANSI-colored console logs for local debugging and simultaneously writes clean, thread-safe logs to individual files via Process IDs (`PID`), ensuring stable log capture during parallel execution (`pytest-xdist`).
* **Advanced Data Modeling:** Implements Python `@dataclass` for representing test entities, allowing for clean object instantiation and dynamic payload overriding.

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
Create a `.env` file in the root directory and add your valid test user credentials:
```env
HEADLESS_MODE=false
ALLOW_MASS_DELETE=false
USER_EMAIL=your_valid_email@gmail.com
USER_PASSWORD=Your_Valid_Password123$
BASE_URL=https://telranedu.web.app
API_URL=https://contactapp-telran-backend.herokuapp.com
```

## 🏃‍♂️ How to Run Tests

**Run all hybrid tests (Selenium UI + API) in parallel:**
```bash
pytest tests/ -n auto --clean-alluredir --alluredir=allure-results
```

**Run modern Playwright tests (headed mode for debugging):**
```bash
pytest tests/test_playwright_login.py -s --headed
```

**Generate and view Allure Report locally:**
```bash
allure serve allure-results
```

## ☁️ CI/CD & Remote Execution
This project is fully integrated with **GitHub Actions**. 
* On every manual trigger (`workflow_dispatch`), the pipeline spins up an Ubuntu runner, installs Chrome, and executes the test suite in parallel Headless mode.
* It securely accesses credentials via **GitHub Secrets**.
* Automatically uploads Log archives as workflow artifacts.
* Generates an Allure report, deploys it to **GitHub Pages**, and sends a notification with the link to Telegram.

## 🏗 Project Structure
```text
QA3553_Phonebook/
├── .github/workflows/    # CI/CD pipeline configuration (tests.yml)
├── api_tests/            # Pure API test suites
├── data/                 # Test data generators (Faker, DataClasses)
├── models/               # Data models (Contact, User)
├── pages/                # Page Object classes (Selenium BasePage & Playwright PwBasePage)
├── tests/                # Hybrid and UI Test suites
├── utils/                # Custom logger, WebDriver listener, API helpers
├── logs/                 # Auto-rotating, thread-safe local log files
├── conftest.py           # Pytest fixtures, Smart Browser Cascading, API Setup
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---
*Author: Maksim Vinogradov*
