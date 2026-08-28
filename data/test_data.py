# файл: data/test_data.py

# ==========================================
# НЕГАТИВНЫЕ СЦЕНАРИИ ДЛЯ КОНТАКТОВ (F5 - F9)
# ==========================================
NEGATIVE_CONTACT_DATA = [
    # --- БЛОК 1: ПУСТЫЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ---
    ("", "Ivanov", "0501234567", "test@mail.com", "Tel Aviv", "desc", "Name cannot be empty!"),
    ("Ivan", "", "0501234567", "test@mail.com", "Tel Aviv", "desc", "Last Name cannot be empty!"),
    ("Ivan", "Ivanov", "", "test@mail.com", "Tel Aviv", "desc", "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
    ("Ivan", "Ivanov", "0501234567", "", "Tel Aviv", "desc", "Email not valid: должно иметь формат адреса электронной почты"),
    ("Ivan", "Ivanov", "0501234567", "test@mail.com", "", "desc", "Address cannot be empty!"),

    # --- БЛОК 2: НЕВЕРНЫЙ ФОРМАТ ДАННЫХ ---
    ("Ivan", "Ivanov", "0501234567", "not-an-email", "Tel Aviv", "desc", "Email not valid: должно иметь формат адреса электронной почты"),
    ("Ivan", "Ivanov", "abcdefghij", "test@mail.com", "Tel Aviv", "desc", "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
    ("Ivan", "Ivanov", "050123", "test@mail.com", "Tel Aviv", "desc", "Phone not valid: Phone number must contain only digits! And length min 10, max 15!"),
]