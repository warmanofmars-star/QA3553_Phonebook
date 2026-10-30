from selenium.webdriver.common.by import By


class ContactFormLocators:
    """Поля формы контакта — одинаковые на странице добавления и в форме редактирования.

    Ключи совпадают с полями модели Contact: форма заполняется в цикле
    по этому словарю, без ручного перечисления полей.
    """

    FIELDS = {
        "name": (By.CSS_SELECTOR, "input[placeholder='Name']"),
        "last_name": (By.CSS_SELECTOR, "input[placeholder='Last Name']"),
        "phone": (By.CSS_SELECTOR, "input[placeholder='Phone']"),
        "email": (By.CSS_SELECTOR, "input[placeholder='email']"),
        "address": (By.CSS_SELECTOR, "input[placeholder='Address']"),
        # *= (содержит): на странице добавления placeholder 'description', в редактировании — 'desc'
        "description": (By.CSS_SELECTOR, "input[placeholder*='desc']"),
    }
