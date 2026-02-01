import logging

from src.storage.constant import VERSION


logger = logging.getLogger(__name__)


class BaseStorageError(Exception):
    def __repr__(self):
        return "Base storrage error."


class MetadataFileError(BaseStorageError):
    def __repr__(self):
        return "Don't find a metadata file."

class InvalidMetadataFileError(BaseStorageError):
    def __repr__(self):
        return "Invalid metadata file."


class VersionMetadataFileError(BaseStorageError):
    def __init__(self, file_version, *args, **kwargs):
        self.file_version = file_version
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"Version mismatch: expected {VERSION}, got {self.file_version}"


class AlreadyExistsError(BaseStorageError):
    def __repr__(self):
        return "Table already exists."

class NoTableFoundError(BaseStorageError):
    def __repr__(self):
        return "Table not exists."
