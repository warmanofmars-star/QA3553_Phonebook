# schemas/contact_schemas.py

# Схема полностью скопирована из Swagger (ContactDto),
# включая найденную недоработку с отсутствием phone и email в массиве required.
CONTACT_OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "lastName": {"type": "string"},
        "email": {"type": "string"},
        "phone": {
            "type": "string",
            "pattern": "^\\d{10,15}$" # Жесткая проверка из Swagger
        },
        "address": {"type": "string"},
        "description": {"type": "string"}
    },
    # Swagger указывает обязательными только эти 3 поля!
    "required": ["address", "lastName", "name"]
}

GET_CONTACTS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "contacts": {
            "type": "array",
            "items": CONTACT_OBJECT_SCHEMA
        }
    }
}