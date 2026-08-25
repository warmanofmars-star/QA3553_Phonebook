from dataclasses import dataclass

@dataclass
class Contact:
    name: str
    last_name: str
    phone: str
    email: str
    address: str
    description: str = "" # Согласно спецификации (T46), это поле необязательное