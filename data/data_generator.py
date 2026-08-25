import random
import string
import time
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
        """Генерирует уникальный валидный email"""
        prefix_length = random.randint(5, 10)
        prefix = ''.join(random.choices(string.ascii_lowercase, k=prefix_length))
        return f"{prefix}_{int(time.time())}@gmail.com"

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


# ==========================================
# ГЕНЕРАТОР ДЛЯ КОНТАКТОВ (Faker + Unique + Numerify)
# ==========================================
class ContactGenerator:

    @classmethod
    def get_random_contact(cls):
        """Возвращает объект Contact с уникальными случайными данными"""
        return Contact(
            name=fake.unique.first_name(),
            last_name=fake.unique.last_name(),
            phone=fake.numerify(text="05########"),
            email=fake.unique.email(),
            address=fake.address().replace('\n', ' '),
            description=fake.sentence(nb_words=5)
        )