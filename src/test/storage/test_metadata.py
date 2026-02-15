import pytest
from unittest.mock import patch
from datetime import datetime

from src.storage.metadata import MetadataController, Metadata, TablesMetadata
from src.errors import MetadataFileError, InvalidMetadataFileError, VersionMetadataFileError
from src.storage import metadata as metadata_module


class TestMetadataControllerInitFile:
    """Tests for MetadataController.init_file() method."""

    def test_init_file_creates_new_file_with_correct_version(self, tmp_path):
        """When metadata file doesn't exist, init_file should create it with current VERSION."""
        metadata_path = tmp_path / "metadata.txt"

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            controller.init_file()

        # Verify file was created with correct format
        assert metadata_path.exists()
        content = metadata_path.read_text()
        assert content == f"version:{metadata_module.VERSION}\n"

    def test_init_file_existing_file_with_matching_version(self, tmp_path):
        """When metadata file exists with matching version, init_file should succeed."""
        metadata_path = tmp_path / "metadata.txt"
        metadata_path.write_text(f"version:{metadata_module.VERSION}\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            # Should not raise any exception
            controller.init_file()

    def test_init_file_existing_file_with_mismatched_version_raises_error(self, tmp_path):
        """When metadata file exists with different version, init_file should raise VersionMetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"
        old_version = "0.0"
        metadata_path.write_text(f"version:{old_version}\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(VersionMetadataFileError):
                controller.init_file()

    def test_init_file_existing_file_without_version_prefix_raises_error(self, tmp_path):
        """When metadata file exists but doesn't start with 'version:', should raise InvalidMetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"
        metadata_path.write_text("invalid_content\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(InvalidMetadataFileError):
                controller.init_file()

    def test_init_file_empty_existing_file_raises_error(self, tmp_path):
        """When metadata file exists but is empty, should raise InvalidMetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"
        metadata_path.write_text("")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(InvalidMetadataFileError):
                controller.init_file()

    def test_init_file_existing_file_with_tables_and_matching_version(self, tmp_path):
        """When metadata file exists with matching version and tables, init_file should succeed."""
        metadata_path = tmp_path / "metadata.txt"
        content = f"version:{metadata_module.VERSION}\nusers|2024-01-01T00:00:00|/storage/users\n"
        metadata_path.write_text(content)

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            # Should not raise any exception
            controller.init_file()

    def test_init_file_version_mismatch_error_message(self, tmp_path):
        """When version mismatch occurs, error message should contain version information."""
        metadata_path = tmp_path / "metadata.txt"
        old_version = "0.0"
        metadata_path.write_text(f"version:{old_version}\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(VersionMetadataFileError) as exc_info:
                controller.init_file()

            # Verify error message contains version info
            error_message = repr(exc_info.value)
            assert metadata_module.VERSION in error_message
            assert old_version in error_message

    def test_init_file_idempotent_with_same_version(self, tmp_path):
        """Calling init_file multiple times with same version should succeed."""
        metadata_path = tmp_path / "metadata.txt"

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()

            # First call - creates file
            controller.init_file()
            content_after_first = metadata_path.read_text()

            # Second call - should not modify or raise
            controller.init_file()
            content_after_second = metadata_path.read_text()

            assert content_after_first == content_after_second


class TestMetadataControllerReadMetadataFile:
    """Tests for MetadataController.read_metadata_file() method."""

    def test_read_metadata_file_not_exists_raises_error(self, tmp_path):
        """When metadata file doesn't exist, should raise MetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(MetadataFileError):
                controller.read_metadata_file()

    def test_read_metadata_file_with_only_version_returns_empty_tables(self, tmp_path):
        """When metadata file has only version line, should return Metadata with empty tables."""
        metadata_path = tmp_path / "metadata.txt"
        metadata_path.write_text(f"version:{metadata_module.VERSION}\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            result = controller.read_metadata_file()

            assert result.version == metadata_module.VERSION
            assert result.tables == []

    def test_read_metadata_file_version_mismatch_raises_error(self, tmp_path):
        """When metadata file has different version, should raise MetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"
        metadata_path.write_text("version:0.0\n")

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)):
            controller = MetadataController()
            with pytest.raises(MetadataFileError):
                controller.read_metadata_file()


class TestMetadataControllerWriteTables:
    """Tests for MetadataController.write_tables_to_metadata_file() method."""

    def test_write_tables_metadata_file_not_exists_raises_error(self, tmp_path):
        """When metadata file doesn't exist, should raise MetadataFileError."""
        metadata_path = tmp_path / "metadata.txt"
        storage_path = tmp_path / "storage"

        with patch.object(metadata_module, "METADATA_PATH", str(metadata_path)), \
             patch.object(metadata_module, "STORAGE_PATH", str(storage_path)):
            controller = MetadataController()
            with pytest.raises(MetadataFileError):
                controller.write_tables_to_metadata_file("users")


class TestMetadataControllerSeparator:
    """Tests for MetadataController.SEPARATOR constant."""

    def test_separator_is_pipe(self):
        """Verify that SEPARATOR is '|'."""
        controller = MetadataController()
        assert controller.SEPARATOR == "|"

    def test_separator_is_class_attribute(self):
        """Verify SEPARATOR is a class attribute."""
        assert MetadataController.SEPARATOR == "|"


class TestMetadataDataclasses:
    """Tests for Metadata and TablesMetadata dataclasses."""

    def test_metadata_dataclass_creation(self):
        """Test that Metadata dataclass can be created correctly."""
        metadata = Metadata(version="0.1", tables=[], exists_tables=set())
        assert metadata.version == "0.1"
        assert metadata.tables == []

    def test_metadata_dataclass_is_frozen(self):
        """Test that Metadata dataclass is immutable."""
        metadata = Metadata(version="0.1", tables=[], exists_tables=set())
        with pytest.raises(AttributeError):
            metadata.version = "0.2"

    def test_tables_metadata_dataclass_creation(self):
        """Test that TablesMetadata dataclass can be created correctly."""
        now = datetime.now()
        table = TablesMetadata(
            table_name="users",
            table_delete_data=now,
            table_creation_data=now,
            pages_path="/storage/users"
        )
        assert table.table_name == "users"
        assert table.table_delete_data == now
        assert table.table_creation_data == now
        assert table.pages_path == "/storage/users"

    def test_tables_metadata_dataclass_is_frozen(self):
        """Test that TablesMetadata dataclass is immutable."""
        now = datetime.now()
        table = TablesMetadata(
            table_name="users",
            table_delete_data=now,
            table_creation_data=now,
            pages_path="/storage/users"
        )
        with pytest.raises(AttributeError):
            table.table_name = "orders"

    def test_metadata_with_tables(self):
        """Test Metadata with a list of TablesMetadata."""
        now = datetime.now()
        tables = [
            TablesMetadata(
                table_name="users",
                table_delete_data=now,
                table_creation_data=now,
                pages_path="/storage/users"
            ),
            TablesMetadata(
                table_name="orders",
                table_delete_data=now,
                table_creation_data=now,
                pages_path="/storage/orders"
            )
        ]
        metadata = Metadata(version="0.1", tables=tables, exists_tables=set())
        assert len(metadata.tables) == 2
        assert metadata.tables[0].table_name == "users"
        assert metadata.tables[1].table_name == "orders"

    def test_tables_metadata_equality(self):
        """Test that TablesMetadata with same values are equal."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        table1 = TablesMetadata(
            table_name="users",
            table_delete_data=now,
            table_creation_data=now,
            pages_path="/storage/users"
        )
        table2 = TablesMetadata(
            table_name="users",
            table_delete_data=now,
            table_creation_data=now,
            pages_path="/storage/users"
        )
        assert table1 == table2

    def test_metadata_equality(self):
        """Test that Metadata with same values are equal."""
        metadata1 = Metadata(version="0.1", tables=[], exists_tables=set())
        metadata2 = Metadata(version="0.1", tables=[], exists_tables=set())
        assert metadata1 == metadata2

    def test_tables_metadata_with_none_delete_data(self):
        """Test TablesMetadata can be created with None for delete_data (active table)."""
        now = datetime.now()
        table = TablesMetadata(
            table_name="users",
            table_delete_data=None,
            table_creation_data=now,
            pages_path="/storage/users"
        )
        assert table.table_delete_data is None
        assert table.table_name == "users"
