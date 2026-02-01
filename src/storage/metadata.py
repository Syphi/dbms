import os

from datetime import datetime
from dataclasses import dataclass

from src.storage.constant import METADATA_PATH, VERSION, STORAGE_PATH
from src.storage.errors import MetadataFileError, InvalidMetadataFileError, AlreadyExistsError


@dataclass(frozen=True)
class Metadata:
    version: str
    tables: list


@dataclass(frozen=True)
class TablesMetadata:
    table_name: str
    table_delete_data: datetime
    table_creation_data: datetime

    pages_path: str


class MetadataController:
    SEPARATOR = "|"

    @staticmethod
    def init_file():
        if not os.path.exists(METADATA_PATH):
            # Create storage directory if it doesn't exist
            os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
            with open(METADATA_PATH, "w") as file:
                file.write(f"version:{VERSION}\n")

        with open(METADATA_PATH, "r") as file:
            first_line = file.readline().strip()
            if first_line.startswith("version:"):
                file_version = first_line.split(":", 1)[1]
                if file_version != VERSION:
                    raise MetadataFileError(
                        f"Version mismatch: expected {VERSION}, got {file_version}"
                    )

            else:
                raise InvalidMetadataFileError

    def read_metadata_file(self) -> Metadata:
        if not os.path.exists(METADATA_PATH):
            raise MetadataFileError

        tables = []
        version = ""
        with open(METADATA_PATH, "r") as file:
            first_line = file.readline().strip()
            if first_line.startswith("version:"):
                version = first_line.split(":", 1)[1]
                if version != VERSION:
                    raise MetadataFileError

                for line in file:
                    table_name, table_delete_data, table_creation_data, pages_path = (line.split(self.SEPARATOR))
                    tables.append(
                        TablesMetadata(
                            table_name=table_name,
                            table_delete_data=datetime.fromisoformat(table_delete_data),
                            table_creation_data=datetime.fromisoformat(table_creation_data),
                            pages_path=pages_path,
                        )
                    )

        return Metadata(
            version=version,
            tables=tables
        )

    def write_tables_to_metadata_file(self, table_name: str):
        _metadata = self.read_metadata_file()
        if table_name in [table.table_name for table in _metadata.tables if not table.table_delete_data]:
            raise AlreadyExistsError

        with open(METADATA_PATH, "r+") as file:
            storage_path = os.path.join(STORAGE_PATH, table_name)
            if os.path.exists(storage_path):
                os.remove(storage_path)

            os.makedirs(storage_path, exist_ok=True)
            file.write(f"{table_name}{self.SEPARATOR}{self.SEPARATOR}{datetime.now().isoformat()}{self.SEPARATOR}{storage_path}{self.SEPARATOR}")

    def delete_table_from_metadata_file(self, table_name: str):
        _metadata = self.read_metadata_file()
        if table_name not in [table.table_name for table in _metadata.tables if not table.table_delete_data]:
            raise NotFoundError

        with open(METADATA_PATH, "r+") as file:
            storage_path = os.path.join(STORAGE_PATH, table_name)
            if os.path.exists(storage_path):
                os.remove(storage_path)

            os.makedirs(storage_path, exist_ok=True)
            file.write(f"{table_name}{self.SEPARATOR}{self.SEPARATOR}{datetime.now().isoformat()}{self.SEPARATOR}{storage_path}{self.SEPARATOR}")
