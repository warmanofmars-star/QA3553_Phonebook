from dataclasses import dataclass

@dataclass
class Contact:
    name: str = None
    last_name: str = None
    phone: str = None
    email: str = None
    address: str = None
    description: str = None # Согласно спецификации (T46), это поле необязательное