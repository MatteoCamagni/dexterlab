from typing import Dict, Tuple

from cerberus import Validator

from ..types.basic import ConnectorCategory

SCHEMA: dict = {
    "name": {"type": "string", "required": True},
    "description": {"type": "string", "required": True},
    "environment": {"type": "dict", "required": True},
    "items": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "keysrules": {"type": "string", "regex": "^[A-Z]\w*$"},
            "valuesrules": {
                "schema": {
                    "name": {"type": "string", "required": True},
                    "pn": {"type": "string", "required": True},
                    "sn": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "group": {"type": "string"},
                },
            },
        },
    },
    "connections": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "item_connector": {"type": "string", "required": True},
                "start": {"type": "string", "required": True},
                "start_port": {"type": "string", "required": True},
                "end": {"type": "string", "required": True},
                "end_port": {"type": "string", "required": True},
                "category": {
                    "type": "string",
                    "required": True,
                    "allowed": [e.name for e in ConnectorCategory],
                },
                "autoconnect": {"type": "boolean", "default": True},
                "manual_only": {"type": "boolean", "default": False},
            },
        },
    },
}


def validate_lab_definition(labdef: dict) -> Tuple[bool, Dict]:
    v = Validator(SCHEMA)
    return v.validate(labdef), v.errors
