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
        space_total, space_left = page_size, page_size
        with open(_path, "w") as file:
            header = Page.SEPARATOR.join([str(max_value), str(min_value), str(space_total), str(space_left)])
            file.write(f"{header}\n")

    @classmethod
    def read_page(cls, path: str) -> "Page":
        with open(path, "r") as file:
            header = file.readline().strip().split(cls.SEPARATOR)
            max_value, min_value, space_total, space_left = map(int, header)

            page_data = []
            for line in file:
                parts = line.strip().split(cls.SEPARATOR)
                row_id = int(parts[0])
                # Try to parse value as int, otherwise keep as string
                try:
                    value = int(parts[1])
                except ValueError:
                    value = parts[1]
                page_data.append((row_id, value))

            return cls(
                path=path,
                max_value=max_value,
                min_value=min_value,
                space_total=space_total,
                space_left=space_left,
                page_data=page_data
            )

    @classmethod
    def read_header(cls, path: str) -> dict:
        with open(path, "r") as file:
            header = file.readline().strip().split(cls.SEPARATOR)
            max_value, min_value, space_total, space_left = map(int, header)
            return {
                "path": path,
                "max_value": max_value,
                "min_value": min_value,
                "space_total": space_total,
                "space_left": space_left,
            }

    def save(self):
        with open(self.path, "w") as file:
            header = self.SEPARATOR.join([
                str(self.max_value),
                str(self.min_value),
                str(self.space_total),
                str(self.space_left),
            ])
            file.write(f"{header}\n")
            for row in self.page_data:
                file.write(f"{self.SEPARATOR.join(map(str, row))}\n")
