from enum import Enum
from dataclasses import dataclass


class DataTypes(Enum):
    INT = "int"
    STR = "str"


class Choose(Enum):
    OR = "OR"
    AND = "AND"


class Comparator(Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    LEFT_MORE = "<"
    LEFT_MORE_EQUAL = "<="
    RIGHT_MORE = ">"
    RIGHT_MORE_EQUAL = ">="


@dataclass
class CreateTableColumExp:
    column_name: str
    column_type: DataTypes
    column_default_value: str | int | None


@dataclass
class CreateTableExp:
    table_name: str
    table_columns: list[CreateTableColumExp]


@dataclass
class InsertValueExp:
    column_name: str
    column_value: str | int


@dataclass
class InsertExp:
    table_name: str
    values_map: list[InsertValueExp]


@dataclass
class SelectWhereExp:
    column_name: str
    compare: Comparator
    value: str | int

    next: "SelectWhereExp"
    next_value: Choose | None


@dataclass
class SelectExp:
    column_names: list[str]
    table_name: str
    where_conditions: SelectWhereExp
    limit: int | None
