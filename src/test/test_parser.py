import pytest

from src.parser.gramatical import parse_sql
from src.parser.ast_schema import (
    CreateTableExp,
    CreateTableColumExp,
    DataTypes,
    InsertExp,
    InsertValueExp,
    SelectExp,
    SelectWhereExp,
    Comparator,
    Choose,
)


class TestParser:
    # ---------- CREATE TABLE Tests ----------
    def test_create_table_basic(self):
        sql = "CREATE TABLE users (id INT, name TEXT);"
        result = parse_sql(sql)

        assert isinstance(result, CreateTableExp)
        assert result.table_name == "users"
        assert len(result.table_columns) == 2

        col1 = result.table_columns[0]
        assert col1.column_name == "id"
        assert col1.column_type == DataTypes.INT

        col2 = result.table_columns[1]
        assert col2.column_name == "name"
        assert col2.column_type == DataTypes.STR

    # ---------- INSERT Tests ----------
    def test_insert_basic(self):
        sql = "INSERT INTO users (id, name) VALUES (1, 'John');"
        result = parse_sql(sql)

        assert isinstance(result, InsertExp)
        assert result.table_name == "users"
        assert len(result.values_map) == 2

        val1 = result.values_map[0]
        assert val1.column_name == "id"
        assert val1.column_value == 1

        val2 = result.values_map[1]
        assert val2.column_name == "name"
        assert val2.column_value == "John"

    def test_insert_quoted_string(self):
        sql = "INSERT INTO messages (content) VALUES ('Hello, World!');"
        result = parse_sql(sql)
        assert result.values_map[0].column_value == "Hello, World!"

    # ---------- SELECT Tests ----------
    def test_select_all(self):
        sql = "SELECT * FROM users;"
        result = parse_sql(sql)

        assert isinstance(result, SelectExp)
        assert result.table_name == "users"
        assert result.column_names == ["*"]
        assert result.where_conditions is None
        assert result.limit is None

    def test_select_columns(self):
        sql = "SELECT id, name FROM users;"
        result = parse_sql(sql)

        assert result.column_names == ["id", "name"]

    def test_select_where_simple(self):
        sql = "SELECT * FROM users WHERE id = 1;"
        result = parse_sql(sql)

        assert result.where_conditions is not None
        cond = result.where_conditions
        assert cond.column_name == "id"
        assert cond.compare == Comparator.EQUAL
        assert cond.value == 1
        assert cond.next is None

    def test_select_where_and(self):
        sql = "SELECT * FROM users WHERE age >= 18 AND status = 'active';"
        result = parse_sql(sql)

        cond1 = result.where_conditions
        assert cond1.column_name == "age"
        assert cond1.compare == Comparator.RIGHT_MORE_EQUAL
        assert cond1.value == 18
        assert cond1.next_value == Choose.AND

        cond2 = cond1.next
        assert cond2 is not None
        assert cond2.column_name == "status"
        assert cond2.compare == Comparator.EQUAL
        assert cond2.value == "active"

    def test_select_where_or(self):
        sql = "SELECT * FROM users WHERE role = 'admin' OR role = 'moderator';"
        result = parse_sql(sql)

        cond1 = result.where_conditions
        assert cond1.column_name == "role"
        assert cond1.value == "admin"
        assert cond1.next_value == Choose.OR

        cond2 = cond1.next
        assert cond2.column_name == "role"
        assert cond2.value == "moderator"

    def test_select_limit(self):
        sql = "SELECT * FROM users LIMIT 10;"
        result = parse_sql(sql)

        assert result.limit == 10

    def test_select_full_complex(self):
        sql = "SELECT id, name FROM users WHERE id > 0 AND active = 1 LIMIT 5;"
        result = parse_sql(sql)

        assert result.table_name == "users"
        assert result.column_names == ["id", "name"]
        assert result.limit == 5

        cond1 = result.where_conditions
        assert cond1.column_name == "id"
        assert cond1.compare == Comparator.RIGHT_MORE
        assert cond1.next_value == Choose.AND
