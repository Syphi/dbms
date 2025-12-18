from src.cli import cli_dbms

"""
Courses: https://www.csosvita.com/courses/database-internals
NOTION: https://www.notion.so/CS-Osvita-Database-Internals-Nov-24-Mar-02-2b4e34ccb1ca818d93d7d28880a5d0b8?pvs=9

CREATE TABLE table_name (
    column_name_1 INT / TEXT / BIGINT,
    column_name_2 INT / TEXT / BIGINT,
);

INSERT INTO table_name (column_name_1, column_name_2) VALUES (value_1, value_2);
value_1 = INT / TEXT ('some text') / NULL

SELECT (1) FROM table_name WHERE (2) LIMIT INT;
1. * | col_1, col_2
2. =, !=, <, <=, >, >=, AND, OR
"""


if __name__ == "__main__":
    """
    ❯ python src/main.py lekser -c "SELECT * FROM table;"
    ❯ python src/main.py input -c "INSERT INTO products (id, title) VALUES (1, 'Book');"
    ❯ python src/main.py input -c "INSERT INTO coords (x, y, z) VALUES (10, 20, 30);"
    ❯ python src/main.py input -c "INSERT INTO coords (x, y, z) VALUES (10, 20, 30. 5);"
    """
    cli_dbms()
