# 📖 Phonebook Hybrid Test Automation Framework

[![UI Tests in Docker](https://github.com/warmanofmars-star/QA3553_Phonebook/actions/workflows/tests.yml/badge.svg)](https://github.com/warmanofmars-star/QA3553_Phonebook/actions)
📊 **Live Allure Report:** [View Dashboard](https://warmanofmars-star.github.io/QA3553_Phonebook/)

Robust, production-ready hybrid test automation framework for the "Phonebook" web application, featuring a fully containerized **Infrastructure as Code (IaC)** approach.

This project demonstrates a **Senior-level approach** to QA automation, combining classic UI testing, API integration, remote browser execution via Selenoid, and modern container orchestration.

## 🛠 Technologies & Tools
* **Language:** Python 3.12+
* **UI Frameworks:** Selenium WebDriver 4+, Playwright (Sync API)
* **API Testing:** Requests
* **Containerization & Orchestration:** Docker, Docker Compose, Selenoid (with video-recorder)
* **Test Runner:** Pytest (with `pytest-xdist` for parallel execution)
* **Design Pattern:** Page Object Model (POM)
* **Test Data:** Faker (dynamic generation of names, phones, emails)
* **Reporting:** Allure Report (with embedded test session videos and secure data masking)
* **CI/CD:** GitHub Actions (Fully containerized pipeline execution)
* **Notifications:** Telegram Bot API
* **Security:** `python-dotenv` for managing sensitive credentials

## 🚀 Key Architectural Features

* **Dockerized Infrastructure (IaC):** The entire test environment—including the framework, Selenoid hub, Chrome instances, and video recording modules—is orchestrated via Docker Compose, guaranteeing absolute environment consistency across local machines and CI/CD.
* **Isolated Networking & Named Volumes:** Utilizes a custom bridge network (`qa-network`) for seamless container communication and persistent `video-data` named volumes to handle test artifacts independently of host OS file systems.
* **Automatic Video Attachment:** Every test execution session is recorded via FFmpeg/Selenoid, and the resulting `.mp4` files are automatically attached to the Allure report upon teardown.
* **Hybrid Testing Approach (API + UI):** Tests use API calls to set up preconditions and manage state, drastically reducing execution time and ensuring test isolation.
* **Smart Browser Cascading:** Automatically detects runtime context (Docker vs. local execution) and supports fallback mechanisms for local debugging.
* **Security & Log Masking:** Sensitive data (passwords, tokens) are strictly masked in all logs and Allure reports.
* **Thread-Safe Custom Logging:** Proprietary logging utility with dual-stream outputs, ANSI-colored console logs, and individual log files per Process ID (`PID`) for safe parallel execution (`pytest-xdist`).

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
docker-compose up --build --exit-code-from qa-framework
```

**Run locally via Pytest (parallel execution):**
```bash
pytest tests/ -n auto --clean-alluredir --alluredir=allure-results
```

**Generate and view Allure Report locally:**
```bash
allure serve allure-results
```

## ☁️ CI/CD & Remote Execution
The project features an advanced **GitHub Actions** pipeline:
* Automatically triggers on `main` branch pushes or manual dispatch (`workflow_dispatch`).
* Spins up a clean Linux runner, builds the Docker Compose stack, and executes all tests in parallel.
* Securely injects credentials via **GitHub Secrets**.
* Generates and deploys the Allure report to **GitHub Pages**.
* Sends automated execution status notifications with a direct link to Telegram.

## 🏗 Project Structure
```text
QA3553_Phonebook/
├── .github/workflows/    # CI/CD pipeline configuration (tests.yml)
├── api_tests/            # Pure API test suites
├── data/                 # Test data generators (Faker, DataClasses)
├── models/               # Data models (Contact, User)
├── pages/                # Page Object classes (Selenium BasePage & Playwright PwBasePage)
├── selenoid/             # Selenoid configuration (browsers.json)
├── tests/                # Hybrid and UI Test suites
├── utils/                # Custom logger, WebDriver listener, API helpers
├── logs/                 # Auto-rotating, thread-safe local log files
├── conftest.py           # Pytest fixtures, Selenoid remote connection, video attachment hooks
├── Dockerfile            # Container definition for the test framework
├── docker-compose.yml    # Infrastructure orchestration (Selenoid + Framework + Network + Volumes)
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---
*Author: Maksim Vinogradov*
