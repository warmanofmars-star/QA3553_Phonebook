from dataclasses import dataclass


@dataclass
class Contact:
    name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None  # Согласно спецификации (T46), это поле необязательное
    # id присваивает бэкенд после создания. У нового (ещё не сохранённого) контакта его нет.
    id: str | None = None

    def to_api_payload(self) -> dict:
        """
        Превращает объект Contact в словарь формата JSON для отправки на API.
        Автоматически маппит python-свойство 'last_name' в API-ключ 'lastName'.
        Поле id добавляется только если оно известно — оно нужно для PUT (обновления),
        а при создании контакта его быть не должно.
        """
        payload = {
            "name": self.name,
            "lastName": self.last_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "description": self.description,
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload
