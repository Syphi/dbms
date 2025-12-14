import pytest
from pathlib import Path
import sys

# Add parent directory to path to import lekser
sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.lekser import read_from_file, read_string


class TestLekser:
    @pytest.mark.parametrize(
        "sql_content",
        [
            "SELECT * FROM table",
            "SELECT * FROM table WHERE id = 1",
            "SELECT * FROM table WHERE id = 1 AND name = 'John'",
            "SELECT * FROM users\nWHERE age > 18\nORDER BY name",
        ],
    )
    def test_read_from_file(self, tmp_path, sql_content):
        test_file = tmp_path / "test_query.sql"
        test_file.write_text(sql_content)

        result = read_from_file(test_file)

        assert result == sql_content

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("SELECT * FROM table", ["SELECT", "*", "FROM", "table"]),
            (
                "SELECT * FROM table WHERE id = 1",
                ["SELECT", "*", "FROM", "table", "WHERE", "id", "=", "1"],
            ),
            (
                "SELECT * FROM table WHERE id = 1 AND name = 'John'",
                [
                    "SELECT",
                    "*",
                    "FROM",
                    "table",
                    "WHERE",
                    "id",
                    "=",
                    "1",
                    "AND",
                    "name",
                    "=",
                    "'John'",
                ],
            ),
            (
                "SELECT * FROM table WHERE -- some random comment -- name = 'John'",
                ["SELECT", "*", "FROM", "table", "WHERE", "name", "=", "'John'"],
            ),
        ],
    )
    def test_read_from_string(self, input, expected):
        assert read_string(input) == expected
