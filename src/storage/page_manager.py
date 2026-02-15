import os
from typing import Generator

from src.errors import NoTableFoundError, NoColumnFoundError, InvalidInputError

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
        if insert_exp.table_name not in _metadata.exists_tables:
            raise NoTableFoundError

        _mapper = self._table_manager.get_table_schema(insert_exp.table_name)
        row_id = self._table_manager.get_next_row_id(insert_exp.table_name)
        for value in insert_exp.values_map:
            self._validate_tuple(value, _mapper)
            self._write_to_free_page(insert_exp.table_name, value, row_id)

    def get(self, table_name: str, row_id: int, columns: list[str] | None = None) -> dict[str, int | str] | None:
        _metadata = self._metadata_controller.read_metadata_file()
        if table_name not in _metadata.exists_tables:
            raise NoTableFoundError

        _mapper = self._table_manager.get_table_schema(table_name)
        if columns is None:
            columns = list(_mapper.keys())


        result = {}
        for column_name in columns:
            column_dir = os.path.join(STORAGE_PATH, table_name, column_name)
            if not os.path.exists(column_dir):
                return None

            found = False
            latest_value = None
            page_files = sorted([f for f in os.listdir(column_dir) if f.endswith(".page")])
            for page_file in page_files:
                page_path = os.path.join(column_dir, page_file)
                header = Page.read_header(page_path)

                if isinstance(row_id, int) and not (header["min_rid"] <= row_id <= header["max_rid"]):
                    continue

                page = Page.read_page(page_path)
                for r, v in page.page_data:
                    if r == row_id:
                        if row_id not in page.page_rids_deleted:
                            latest_value = v
                            found = True

            if not found:
                return None
            result[column_name] = latest_value

        return result

    def get_columns(self, table_name: str, row_id: int, columns: list[str]) -> dict[str, int | str] | None:
        if not columns:
            raise NoColumnFoundError
        return self.get(table_name, row_id, columns)

    def update(self, table_name: str, row_id: int, new_record: dict[str, int | str]) -> int | None:
        if not self.get(table_name, row_id):
            return None

        _mapper = self._table_manager.get_table_schema(table_name)
        self.delete_tuple(table_name, row_id)
        new_row_id = self._table_manager.get_next_row_id(table_name)
        for column_name, column_value in new_record.items():
            val_exp = InsertValueExp(column_name=column_name, column_value=column_value)
            self._validate_tuple(val_exp, _mapper)
            self._write_to_free_page(table_name, val_exp, new_row_id)

        return new_row_id

    def delete_tuple(self, table_name: str, row_id: int):
        _mapper = self._table_manager.get_table_schema(table_name)

        for column_name in _mapper.keys():
            for page in self.scan_column(table_name, column_name):
                if row_id in page.page_rids_deleted:
                    break

                found = False
                for (_row_id, _) in page.page_data:
                    if _row_id == row_id:
                        page.page_rids_deleted.add(row_id)
                        page.save()
                        found = True
                        break

                if found:
                    break

    def scan_column(self, table_name: str, column_name: str) -> Generator[Page, None, None]:
        _mapper = self._table_manager.get_table_schema(table_name)
        if not column_name in _mapper:
            raise NoColumnFoundError

        column_dir = os.path.join(STORAGE_PATH, table_name, column_name)
        if not os.path.exists(column_dir):
            raise NoColumnFoundError

        page_files = sorted([f for f in os.listdir(column_dir) if f.endswith(".page")])
        for page_file in page_files:
            page_path = os.path.join(column_dir, page_file)
            yield Page.read_page(page_path)

    def scan(self, table_name: str, columns: list[str] | None = None) -> Generator[tuple[int, dict[str, int | str]], None, None]:
        _metadata = self._metadata_controller.read_metadata_file()
        if table_name not in _metadata.exists_tables:
            raise NoTableFoundError

        _mapper = self._table_manager.get_table_schema(table_name)
        if columns is None:
            columns = list(_mapper.keys())

        first_column = columns[0]
        rid_data: dict[int, dict[str, int | str]] = {}
        tombstoned_rids: set[int] = set()

        for page in self.scan_column(table_name, first_column):
            tombstoned_rids.update(page.page_rids_deleted)
            for row_id, value in page.page_data:
                if row_id not in tombstoned_rids:
                    rid_data[row_id] = {first_column: value}

        for rid in tombstoned_rids:
            rid_data.pop(rid, None)

        for column_name in columns[1:]:
            column_tombstones: set[int] = set()
            for page in self.scan_column(table_name, column_name):
                column_tombstones.update(page.page_rids_deleted)
                for row_id, value in page.page_data:
                    if row_id in rid_data and row_id not in column_tombstones:
                        rid_data[row_id][column_name] = value

        for row_id in sorted(rid_data.keys()):
            record = rid_data[row_id]
            if len(record) == len(columns):
                yield (row_id, record)

    @staticmethod
    def _validate_tuple(value: InsertValueExp, mapper: dict[str, tuple[str, str]]):
        if value.column_name not in mapper:
            raise NoColumnFoundError

        column_type, column_default_value = mapper[value.column_name]
        if column_type == "int" and not isinstance(value.column_value, int):
            raise InvalidInputError
        elif column_type == "str" and not isinstance(value.column_value, str):
            raise InvalidInputError

    def _write_to_free_page(self, table_name: str, value: InsertValueExp, row_id: int):
        column_dir = os.path.join(STORAGE_PATH, table_name, value.column_name)
        data_size = self._calculate_data_size(value.column_value, row_id)

        page_path = self._find_free_page(column_dir, data_size)
        if page_path is None:
            Page.create_page(table_name, value.column_name)
            page_path = self._find_free_page(column_dir, data_size)

        self._append_to_page(page_path, value.column_value, row_id)

    @staticmethod
    def _find_free_page(column_dir: str, required_space: int) -> str | None:
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

        if not page.page_data or len(page.page_data) == 1:
            page.min_rid = row_id
            page.max_rid = row_id
        else:
            page.min_rid = min(page.min_rid, row_id)
            page.max_rid = max(page.max_rid, row_id)

        page.save()

    @staticmethod
    def _calculate_data_size(value: str | int, row_id: int) -> int:
        return len(str(row_id)) + 1 + len(str(value)) + 1
