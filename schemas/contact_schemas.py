CONTACT_OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "lastName": {"type": "string"},
        "email": {"type": "string"},
        "phone": {
            "type": "string",
            "pattern": "^\\d{10,15}$"
        },
        "address": {"type": "string"},
        "description": {"type": "string"}
    },
    "required": ["address", "lastName", "name"],
    "additionalProperties": False
}

GET_CONTACTS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "contacts": {
            "type": "array",
            "items": CONTACT_OBJECT_SCHEMA
        }
    },
    "required": ["contacts"],
    "additionalProperties": False
}

MESSAGE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"}
    },
    "required": ["message"],
    "additionalProperties": False
}