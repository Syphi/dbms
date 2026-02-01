import pytest
import sys
from pathlib import Path

# Add project root to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

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
    ParseError,
)


class TestGrammaticalCoverage:
    def test_create_table_single_int_column(self):
        sql = "CREATE TABLE users (id INT);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == CreateTableExp(
            table_name="users",
            table_columns=[
                CreateTableColumExp(
                    column_name="id",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                )
            ],
        )

    def test_create_table_multiple_columns_mixed(self):
        sql = "CREATE TABLE products (id INT, name TEXT, price INT);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == CreateTableExp(
            table_name="products",
            table_columns=[
                CreateTableColumExp(
                    column_name="id",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="name",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="price",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
            ],
        )

    def test_create_table_all_text_columns(self):
        sql = "CREATE TABLE log_entries (message TEXT, level TEXT);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == CreateTableExp(
            table_name="log_entries",
            table_columns=[
                CreateTableColumExp(
                    column_name="message",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="level",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
            ],
        )

    def test_create_table_underscore_names(self):
        sql = "CREATE TABLE my_custom_table (user_id INT, first_name TEXT);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == CreateTableExp(
            table_name="my_custom_table",
            table_columns=[
                CreateTableColumExp(
                    column_name="user_id",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="first_name",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
            ],
        )

    def test_create_table_many_columns(self):
        sql = "CREATE TABLE big_table (a INT, b INT, c INT, d TEXT, e TEXT);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == CreateTableExp(
            table_name="big_table",
            table_columns=[
                CreateTableColumExp(
                    column_name="a",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="b",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="c",
                    column_type=DataTypes.INT,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="d",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
                CreateTableColumExp(
                    column_name="e",
                    column_type=DataTypes.STR,
                    column_default_value=None,
                ),
            ],
        )

    # ==========================================
    # INSERT Tests (Min 5)
    # ==========================================

    def test_insert_single_value(self):
        sql = "INSERT INTO simple_table (col1) VALUES (100);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == InsertExp(
            table_name="simple_table",
            values_map=[InsertValueExp(column_name="col1", column_value=100)],
        )

    def test_insert_mixed_values(self):
        sql = "INSERT INTO users (id, name) VALUES (1, 'Alice');"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == InsertExp(
            table_name="users",
            values_map=[
                InsertValueExp(column_name="id", column_value=1),
                InsertValueExp(column_name="name", column_value="Alice"),
            ],
        )

    def test_insert_multiple_strings(self):
        sql = "INSERT INTO logs (level, msg) VALUES ('INFO', 'System started');"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == InsertExp(
            table_name="logs",
            values_map=[
                InsertValueExp(column_name="level", column_value="INFO"),
                InsertValueExp(column_name="msg", column_value="System started"),
            ],
        )

    def test_insert_multiple_integers(self):
        sql = "INSERT INTO coords (x, y, z) VALUES (10, 20, 30);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == InsertExp(
            table_name="coords",
            values_map=[
                InsertValueExp(column_name="x", column_value=10),
                InsertValueExp(column_name="y", column_value=20),
                InsertValueExp(column_name="z", column_value=30),
            ],
        )

    def test_insert_values_match_columns_order(self):
        sql = "INSERT INTO metrics (cpu, memory) VALUES (45, 1024);"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == InsertExp(
            table_name="metrics",
            values_map=[
                InsertValueExp(column_name="cpu", column_value=45),
                InsertValueExp(column_name="memory", column_value=1024),
            ],
        )

    def test_select_wildcard(self):
        sql = "SELECT * FROM users;"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == SelectExp(
            column_names=["*"], table_name="users", where_conditions=None, limit=None
        )

    def test_select_specific_columns(self):
        sql = "SELECT name, email FROM users;"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == SelectExp(
            column_names=["name", "email"],
            table_name="users",
            where_conditions=None,
            limit=None,
        )

    def test_select_with_simple_where(self):
        sql = "SELECT * FROM orders WHERE amount > 100;"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == SelectExp(
            column_names=["*"],
            table_name="orders",
            where_conditions=SelectWhereExp(
                column_name="amount",
                compare=Comparator.RIGHT_MORE,
                value=100,
                next=None,
                next_value=None,
            ),
            limit=None,
        )

    def test_select_with_limit_only(self):
        sql = "SELECT id FROM logs LIMIT 50;"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == SelectExp(
            column_names=["id"], table_name="logs", where_conditions=None, limit=50
        )

    def test_select_complex_where_and_limit(self):
        sql = "SELECT * FROM products WHERE price >= 10 AND stock < 5 LIMIT 20;"
        result = parse_sql(sql)
        assert result.error is None
        assert result.result == SelectExp(
            column_names=["*"],
            table_name="products",
            where_conditions=SelectWhereExp(
                column_name="price",
                compare=Comparator.RIGHT_MORE_EQUAL,
                value=10,
                next=SelectWhereExp(
                    column_name="stock",
                    compare=Comparator.LEFT_MORE,
                    value=5,
                    next=None,
                    next_value=None,
                ),
                next_value=Choose.AND,
            ),
            limit=20,
        )


class TestGrammaticalCoverageWithErrors:
    def test_parse_error_invalid_syntax(self):
        sql = "CREATE TABLE users (id INT"  # Missing closing parenthesis
        result = parse_sql(sql)
        assert result.result is None
        assert isinstance(result.error, ParseError)
        assert (
            "Unexpected end of input" in result.error.msg
            or "Unexpected token" in result.error.msg
        )

    def test_parse_error_missing_semicolon(self):
        sql = "SELECT * FROM users"
        result = parse_sql(sql)
        assert result.result is None
        assert isinstance(result.error, ParseError)
        assert (
            "Unexpected end of input" in result.error.msg
            or "Unexpected token" in result.error.msg
        )

    def test_parse_error_nonsense_query(self):
        sql = "FLIBBERTY GIBBET;"
        result = parse_sql(sql)
        assert result.result is None
        assert isinstance(result.error, ParseError)
        assert (
            "No terminal matches" in result.error.msg
            or "Unexpected token" in result.error.msg
            or "Unexpected characters" in result.error.msg
        )
