from dataclasses import dataclass


@dataclass
class User:
    email: str
    password: str

    def to_api_payload(self) -> dict:
        """Превращает объект User в словарь формата JSON для авторизации/регистрации через API."""
        return {
            "username": self.email,
            "password": self.password
        }