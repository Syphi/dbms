from src.errors import NoTableFoundError, NoColumnFoundError, InvalidInputError
import os

from src.parser.ast_schema import InsertExp, InsertValueExp
from src.storage.metadata import MetadataController
from src.storage.table_manager import TableManager
from src.storage.constant import STORAGE_PATH
from src.storage.page_schema import Page


class PageManager:
    SEPARATOR = "|"

    def __init__(self, metadata_controller: MetadataController, table_manager: TableManager):
        self._metadata_controller = metadata_controller
        self._table_manager = table_manager

    def write_tuple(self, insert_exp: InsertExp):
        _metadata = self._metadata_controller.read_metadata_file()
        print(_metadata)
        if insert_exp.table_name not in _metadata.exists_tables:
            raise NoTableFoundError

        _mapper = self._table_manager.get_table_schema(insert_exp.table_name)
        for value in insert_exp.values_map:
            self._validate_tuple(value, _mapper)
            self._write_to_free_page(insert_exp.table_name, value)

    def _validate_tuple(self, value: InsertValueExp, mapper: dict[str, tuple[str, str]]):
        if value.column_name not in mapper:
            raise NoColumnFoundError

        column_type, column_default_value = mapper[value.column_name]
        if column_type == "int" and not isinstance(value.column_value, int):
            raise InvalidInputError
        elif column_type == "str" and not isinstance(value.column_value, str):
            raise InvalidInputError

    def _write_to_free_page(self, table_name: str, value: InsertValueExp):
        row_id = self._table_manager.get_next_row_id(table_name)
        column_dir = os.path.join(STORAGE_PATH, table_name, value.column_name)
        data_size = self._calculate_data_size(value.column_value, row_id)

        page_path = self._find_free_page(column_dir, data_size)
        if page_path is None:
            Page.create_page(table_name, value.column_name)
            page_path = self._find_free_page(column_dir, data_size)

        self._append_to_page(page_path, value.column_value, row_id)

    def _find_free_page(self, column_dir: str, required_space: int) -> str | None:
        if not os.path.exists(column_dir):
            return None

        page_files = sorted([f for f in os.listdir(column_dir) if f.endswith(".page")])
        for page_file in page_files:
            page_path = os.path.join(column_dir, page_file)
            header = Page.read_header(page_path)
            if header["space_left"] >= required_space:
                return page_path

        return None

    def _append_to_page(self, page_path: str, value: str | int, row_id: int):
        page = Page.read_page(page_path)
        page.page_data.append((row_id, value))

        data_size = self._calculate_data_size(value, row_id)
        page.space_left -= data_size

        if isinstance(value, int):
            if not page.page_data or len(page.page_data) == 1:
                page.min_value = value
                page.max_value = value
            else:
                page.min_value = min(page.min_value, value)
                page.max_value = max(page.max_value, value)

        page.save()

    def _calculate_data_size(self, value: str | int, row_id: int) -> int:
        return len(str(row_id)) + 1 + len(str(value)) + 1
