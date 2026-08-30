# 📖 Phonebook UI Auto-tests

[![Phonebook UI Tests](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

UI Automation testing project for the "Phonebook" web application. 
Developed using **Python**, **Selenium WebDriver**, and **Pytest** following the **Page Object Model (POM)** design pattern.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **Core Framework:** Selenium WebDriver 4+
* **Test Runner:** Pytest
* **Design Pattern:** Page Object Model (POM)
* **Test Data:** Faker (dynamic generation of names, phones, emails)
* **Reporting:** pytest-html
* **CI/CD:** GitHub Actions (with Headless browser execution)
* **Notifications:** Telegram Bot API

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