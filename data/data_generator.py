import random
import string
import uuid
import os
import json
from faker import Faker

# Импортируем наши модели
from models.user import User
from models.contact import Contact

# Инициализируем Faker один раз для всего файла
fake = Faker('en_US')

class UserGenerator:

    @staticmethod
    def generate_valid_password():
        """Генерирует валидный пароль: 8-15 символов, 1 заглавная, 1 строчная, 1 цифра, 1 спецсимвол"""
        upper = random.choice(string.ascii_uppercase)
        lower = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = random.choice("@$#^&*!")

        length = random.randint(8, 15)
        rest_length = length - 4
        all_chars = string.ascii_letters + string.digits + "@$#^&*!"
        rest = ''.join(random.choices(all_chars, k=rest_length))

        password_list = list(upper + lower + digit + special + rest)
        random.shuffle(password_list)

        return ''.join(password_list)

    @staticmethod
    def generate_valid_email():
        """Генерирует абсолютно уникальный email, безопасный для xdist"""
        # uuid4().hex дает уникальную строку из 32 символов. Берем первые 10.
        unique_id = uuid.uuid4().hex[:10]
        return f"user_{unique_id}@gmail.com"

    @classmethod
    def get_valid_user(cls):
        """Возвращает объект User с полностью валидными данными"""
        return User(email=cls.generate_valid_email(), password=cls.generate_valid_password())

    @classmethod
    def get_user_with_invalid_email(cls):
        """Возвращает объект User с невалидным email и валидным паролем"""
        return User(email="invalid_email.com", password=cls.generate_valid_password())

    @classmethod
    def get_user_with_invalid_password(cls):
        """Возвращает объект User с валидным email и коротким невалидным паролем"""
        return User(email=cls.generate_valid_email(), password="123")

    @staticmethod
    def save_user_credentials(user, file_path="data/valid_users.jsonl"):
        """Потокобезопасное сохранение кредов в единый файл формата JSON Lines."""

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Подготавливаем словарь с нужными данными
        user_data = {
            "email": user.email,
            "password": user.password
        }

        # Режим 'a' (append) и запись строки (json.dumps) за одно атомарное действие
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(user_data) + "\n")


# ==========================================
# ГЕНЕРАТОР ДЛЯ КОНТАКТОВ (Faker + Unique + Numerify)
# ==========================================
class ContactGenerator:

    @staticmethod
    def get_random_contact(**overrides) -> Contact:
        """Генерирует случайный контакт с потокобезопасной уникальностью (UUID)"""

        # Получаем абсолютно уникальное число из UUID (int) и берем 8 цифр
        unique_digits = str(uuid.uuid4().int)[:8]
        safe_phone = f"05{unique_digits}"  # Гарантированно 10 цифр, начинается с 05

        data = {
            "name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": safe_phone,  # Прощай, нестабильный fake.unique!
            "email": UserGenerator.generate_valid_email(),
            "address": fake.address(),
            "description": fake.sentence()
        }

        data.update(overrides)
        return Contact(**data)