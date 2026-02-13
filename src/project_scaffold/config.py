from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

SCAFFOLD_METADATA_FILE = ".scaffold.json"

DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASSWORD = "postgres"

SQLALCHEMY_TYPES_MAP = {
    "str": "String",
    "string": "String",
    "int": "Integer",
    "integer": "Integer",
    "float": "Float",
    "bool": "Boolean",
    "boolean": "Boolean",
    "date": "Date",
    "datetime": "DateTime",
    "text": "Text",
    "uuid": "Uuid",
}

PYDANTIC_TYPES_MAP = {
    "str": "str",
    "string": "str",
    "int": "int",
    "integer": "int",
    "float": "float",
    "bool": "bool",
    "boolean": "bool",
    "date": "date",
    "datetime": "datetime",
    "text": "str",
    "uuid": "UUID",
}
