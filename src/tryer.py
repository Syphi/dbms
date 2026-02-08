import random

from src.parser.gramatical import parse_sql
from src.storage import metadata_controller, table_manager, page_manager

# # 1. Create table
# create_sql = "CREATE TABLE users (id INT, name TEXT);"
# parsed_create = parse_sql(create_sql)
# print(f"Creating table: {parsed_create.result}")
# table_manager.create_table(parsed_create.result)
# print("Table created!")

# 2. Insert values
for i in range(10_000):

    first_names = ('John', 'Andy', 'Joe')
    last_names = ('Johnson', 'Smith', 'Williams')
    name = f"{random.choice(first_names)} {random.choice(last_names)}"

    insert_sql_1 = f"INSERT INTO users (id, name) VALUES ({i}, '{name}');"
    print(insert_sql_1)
    parsed_insert_1 = parse_sql(insert_sql_1)
    print(f"Inserting tuple: {parsed_insert_1.result}")
    page_manager.write_tuple(parsed_insert_1.result)

