import os

from src.storage import constant
from src.storage.metadata import MetadataController
from src.parser.ast_schema import CreateTableExp
from src.storage.page_schema import Page


class TableManager:
    column_separator = "|"
    schema_file_name = "schema.txt"
    row_counter_file_name = "row_counter.txt"

    def __init__(self, metadata_controller: MetadataController):
        self._metadata_controller = metadata_controller

    def create_table(self, table_expression: CreateTableExp):
        self._metadata_controller.write_tables_to_metadata_file(table_expression.table_name)
        self._create_table_schema_definition(table_expression)
        self._init_row_counter(table_expression.table_name)
        for _column in table_expression.table_columns:
            Page.create_page(table_expression.table_name, _column.column_name)

    def drop_table(self, table_name: str):
        self._metadata_controller.delete_table_from_metadata_file(table_name)

    def get_table_schema(self, table_name: str) -> dict[str, tuple[str, str]]:
        schema_file_path = os.path.join(constant.STORAGE_PATH, table_name, self.schema_file_name)
        _mapper = {}
        with open(schema_file_path, "r") as schema_file:
            for line in schema_file:
                line = line.strip()
                if not line:
                    continue
                column_name, column_type, column_default_value = line.split(self.column_separator)
                _mapper[column_name] = (column_type, column_default_value)
            return _mapper

    def get_next_row_id(self, table_name: str) -> int:
        counter_path = os.path.join(constant.STORAGE_PATH, table_name, self.row_counter_file_name)
        with open(counter_path, "r") as f:
            current_id = int(f.read().strip())

        next_id = current_id + 1
        with open(counter_path, "w") as f:
            f.write(str(next_id))

        return next_id

    def _init_row_counter(self, table_name: str):
        counter_path = os.path.join(constant.STORAGE_PATH, table_name, self.row_counter_file_name)
        with open(counter_path, "w") as f:
            f.write("0")

    def _create_table_schema_definition(self, table: CreateTableExp):
        if not os.path.exists(os.path.join(constant.STORAGE_PATH, table.table_name)):
            os.makedirs(os.path.join(constant.STORAGE_PATH, table.table_name))

        schema_file_path = os.path.join(constant.STORAGE_PATH, table.table_name, self.schema_file_name)
        if os.path.exists(schema_file_path):
            os.remove(schema_file_path)

        with open(schema_file_path, "w") as schema_file:
            for _column in table.table_columns:
                column_definition = (
                    f"{_column.column_name}{self.column_separator}"
                    f"{_column.column_type}{self.column_separator}"
                    f"{_column.column_default_value or '_'}\n"
                )
                schema_file.write(column_definition)
