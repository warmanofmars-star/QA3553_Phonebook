from dataclasses import dataclass

@dataclass
class Contact:
    name: str = None
    last_name: str = None
    phone: str = None
    email: str = None
    address: str = None
    description: str = None # Согласно спецификации (T46), это поле необязательное

    def to_api_payload(self) -> dict:
        """
        Превращает объект Contact в словарь формата JSON для отправки на API.
        Автоматически маппит python-свойство 'last_name' в API-ключ 'lastName'.
        """
        return {
            "name": self.name,
            "lastName": self.last_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "description": self.description
        }