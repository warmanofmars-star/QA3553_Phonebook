# 📖 Phonebook UI Auto-tests

[![Phonebook UI Tests](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

UI Automation testing project for the "Phonebook" web application.
Developed using **Python**, **Selenium WebDriver**, and **Pytest** following the **Page Object Model (POM)** design pattern.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **Core Framework:** Selenium WebDriver 4+
* **Test Runner:** Pytest (with `pytest-rerunfailures` for flaky tests)
* **Design Pattern:** Page Object Model (POM)
* **Test Data:** Faker (dynamic generation of names, phones, emails)
* **Reporting:** Allure Report (Tests categorized by Severity: BLOCKER, CRITICAL, NORMAL)
* **CI/CD:** GitHub Actions (Automated runs with Headless browser execution)
* **Notifications:** Telegram Bot API
* **Security:** `python-dotenv` for managing sensitive credentials

## 🚀 Quick Start (Local Execution)

### 1. Clone and Setup
```bash
git clone (https://github.com/warmanofmars-star/QA3553_Phonebook.git)
cd QA3553_Phonebook
python -m venv .venv
source .venv/Scripts/activate  # For Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
The project uses hidden credentials. Create a `.env` file in the root directory and add your valid test user credentials:
```env
ALLOW_MASS_DELETE=false
HEADLESS_MODE=true
USER_EMAIL=your_valid_email@gmail.com
USER_PASSWORD=Your_Valid_Password123$
BASE_URL=(https://telranedu.web.app)
```
*💡 **Note:** Set `HEADLESS_MODE=true` if you want to run tests in the background without opening the browser window.*
*💡 **Note:** Set `ALLOW_MASS_DELETE=false` if you want to delete all contacts in contacts page

### 3. Run Tests & View Report
Run the test suite with 2 retries for flaky tests and generate the Allure results:
```bash
pytest tests/ --clean-alluredir --reruns 2 --reruns-delay 2 --alluredir=allure-results
```
Serve the Allure report in your browser:
```bash
allure serve allure-results
```

## ☁️ CI/CD & Remote Execution
This project is fully integrated with **GitHub Actions**. 
* On every manual trigger (`workflow_dispatch`), the pipeline spins up an Ubuntu runner, installs Microsoft Edge, and executes the test suite in Headless mode.
* It securely accesses credentials via **GitHub Secrets**.
* Upon completion, it automatically generates an Allure report, deploys it to **GitHub Pages**, and sends a notification with the link to Telegram.

## 📋 Test Coverage
The project includes both positive and negative scenarios covering the core CRUD operations and security features:
* **Authentication:** User Login, Registration, Logout & Security redirects.
* **Contacts Management:** 
  * Creating new contacts.
  * Editing existing contacts (with dynamic field updates).
  * Deleting contacts.
* **Bug Tracking:** Known frontend bugs (e.g., lack of required fields validation during editing, saving duplicates) are isolated and documented using `@pytest.mark.xfail`.

## 🏗 Project Structure
```text
QA3553_Phonebook/
├── .github/workflows/    # CI/CD pipeline configuration (tests.yml)
├── data/                 # Data generators and static files (Faker, CSV)
├── models/               # Data models (Contact, User)
├── pages/                # Page Object classes (base_page, login_page, contacts_page)
├── tests/                # Test suites (test_login, test_add, test_edit, test_logout)
├── conftest.py           # Pytest fixtures and WebDriver setup (UI & Headless modes)
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```
