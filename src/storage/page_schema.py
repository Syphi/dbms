import os

from dataclasses import dataclass, field

from src.storage.constant import STORAGE_PATH


@dataclass
class Page:
    path: str
    max_value: int
    min_value: int
    space_total: int
    space_left: int
    max_rid: int = 0
    min_rid: int = 0
    page_rids_deleted: set[int] = field(default_factory=set)

    SEPARATOR = "|"
    page_data: list[tuple] = field(default_factory=list)

    @staticmethod
    def create_page(table_name: str, column_name: str, initial_number: int = 0, page_size: int = 4096):
        os.makedirs(os.path.join(STORAGE_PATH, table_name, column_name), exist_ok=True)
        _path = os.path.join(STORAGE_PATH, table_name, column_name, f"{column_name}_{initial_number}.page")
        while os.path.exists(_path):
            initial_number += 1
            _path = os.path.join(STORAGE_PATH, table_name, column_name, f"{column_name}_{initial_number}.page")

        max_value, min_value = 0, 0
        max_rid, min_rid = 0, 0
        space_total, space_left = page_size, page_size
        page_rids_deleted = ""
        with open(_path, "w") as file:
            header = Page.SEPARATOR.join([
                str(max_value), str(min_value), str(space_total), str(space_left),
                str(max_rid), str(min_rid),
                page_rids_deleted
            ])
            file.write(f"{header}\n")

    @classmethod
    def read_page(cls, path: str) -> "Page":
        with open(path, "r") as file:
            header = file.readline().strip().split(cls.SEPARATOR)
            max_value, min_value, space_total, space_left, max_rid, min_rid, page_rids_deleted_str = header
            
            page_rids_deleted = set()
            if page_rids_deleted_str:
                 page_rids_deleted = set(map(int, page_rids_deleted_str.split(",")))

            page_data = []
            for line in file:
                parts = line.strip().split(cls.SEPARATOR)
                row_id = int(parts[0])
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                page_data.append((row_id, value))

            return cls(
                path=path,
                max_value=int(max_value),
                min_value=int(min_value),
                space_total=int(space_total),
                space_left=int(space_left),
                max_rid=int(max_rid),
                min_rid=int(min_rid),
                page_rids_deleted=page_rids_deleted,
                page_data=page_data,
            )

    @classmethod
    def read_header(cls, path: str) -> dict:
        with open(path, "r") as file:
            header = file.readline().strip().split(cls.SEPARATOR)
            max_value, min_value, space_total, space_left, max_rid, min_rid, page_rids_deleted_str = header
            
            page_rids_deleted = set()
            if page_rids_deleted_str:
                 page_rids_deleted = set(map(int, page_rids_deleted_str.split(",")))
            
            return {
                "path": path,
                "max_value": int(max_value),
                "min_value": int(min_value),
                "space_total": int(space_total),
                "space_left": int(space_left),
                "max_rid": int(max_rid),
                "min_rid": int(min_rid),
                "page_rids_deleted": page_rids_deleted
            }

    def save(self):
        with open(self.path, "w") as file:
            deleted_rids_str = ",".join(map(str, self.page_rids_deleted))
            header = self.SEPARATOR.join([
                str(self.max_value),
                str(self.min_value),
                str(self.space_total),
                str(self.space_left),
                str(self.max_rid),
                str(self.min_rid),
                deleted_rids_str
            ])
            file.write(f"{header}\n")
            for row in self.page_data:
                file.write(f"{self.SEPARATOR.join(map(str, row))}\n")
