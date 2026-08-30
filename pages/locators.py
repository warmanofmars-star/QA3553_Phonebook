from selenium.webdriver.common.by import By


class ContactFormLocators:
    """Общие локаторы для формы контакта (создание и редактирование)"""

    FIELDS = {
        "name": (By.CSS_SELECTOR, "input[placeholder='Name']"),
        "last_name": (By.CSS_SELECTOR, "input[placeholder='Last Name']"),
        "phone": (By.CSS_SELECTOR, "input[placeholder='Phone']"),
        "email": (By.CSS_SELECTOR, "input[placeholder='email']"),
        "address": (By.CSS_SELECTOR, "input[placeholder='Address']"),
        # Используем *= (содержит), чтобы покрыть и 'desc' и 'description'
        "description": (By.CSS_SELECTOR, "input[placeholder*='desc']")
    }