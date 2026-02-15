
import pytest
from unittest.mock import patch

from src.storage.metadata import MetadataController
from src.storage.table_manager import TableManager
from src.storage.page_manager import PageManager
from src.parser.ast_schema import CreateTableExp, CreateTableColumExp, DataTypes, InsertExp, InsertValueExp
from src.storage import metadata as metadata_module
from src.storage import constant as constant_module

class TestStorage:
    @pytest.fixture
    def setup_storage(self, tmp_path):
        self.metadata_path = tmp_path / "metadata.txt"
        self.storage_path = tmp_path / "storage"
        self.storage_path.mkdir()
        
        # Patch constants
        self.metadata_patcher = patch.object(metadata_module, "METADATA_PATH", str(self.metadata_path))
        self.storage_constant_patcher = patch.object(constant_module, "STORAGE_PATH", str(self.storage_path))
        self.metadata_storage_patcher = patch("src.storage.metadata.STORAGE_PATH", str(self.storage_path))
        self.page_manager_patcher = patch("src.storage.page_manager.STORAGE_PATH", str(self.storage_path))
        self.page_schema_patcher = patch("src.storage.page_schema.STORAGE_PATH", str(self.storage_path))

        self.metadata_patcher.start()
        self.storage_constant_patcher.start()
        self.metadata_storage_patcher.start()
        self.page_manager_patcher.start()
        self.page_schema_patcher.start()

        # Initialize controller
        self.metadata_controller = MetadataController()
        self.metadata_controller.init_file()
        self.table_manager = TableManager(self.metadata_controller)
        self.page_manager = PageManager(self.metadata_controller, self.table_manager)

        yield

        self.metadata_patcher.stop()
        self.storage_constant_patcher.stop()
        self.metadata_storage_patcher.stop()
        self.page_manager_patcher.stop()
        self.page_schema_patcher.stop()

    def test_create_table(self, setup_storage):
        table_name = "users"
        columns = [
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
        create_exp = CreateTableExp(table_name, columns)
        
        self.table_manager.create_table(create_exp)
        
        # Verify schema file created
        schema_path = self.storage_path / table_name / "schema.txt"
        assert schema_path.exists()
        content = schema_path.read_text()
        assert "id|int|_" in content
        assert "name|str|_" in content

    def test_insert_and_scan(self, setup_storage):
        # 1. Create Table
        table_name = "users"
        columns = [
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
        self.table_manager.create_table(CreateTableExp(table_name, columns))

        # 2. Insert Data
        insert_exp = InsertExp(table_name, [
            InsertValueExp("id", 1),
            InsertValueExp("name", "Alice")
        ])
        self.page_manager.write_tuple(insert_exp)

        insert_exp2 = InsertExp(table_name, [
            InsertValueExp("id", 2),
            InsertValueExp("name", "Bob")
        ])
        self.page_manager.write_tuple(insert_exp2)

        # 3. Scan Column
        # API: scan_column(table_name, column_name) -> Generator[Page]
        # Each Page has page_data: list[(rid, value)] and page_rids_deleted: set[int]
        ids = []
        for page in self.page_manager.scan_column(table_name, "id"):
            for rid, val in page.page_data:
                if rid not in page.page_rids_deleted:
                    ids.append((rid, {'id': val}))

        names = []
        for page in self.page_manager.scan_column(table_name, "name"):
            for rid, val in page.page_data:
                if rid not in page.page_rids_deleted:
                    names.append((rid, {'name': val}))

        assert len(ids) == 2
        # ids is list of (rid, {'id': val})
        assert (1, {'id': 1}) in ids
        assert (2, {'id': 2}) in ids

        assert len(names) == 2
        assert (1, {'name': 'Alice'}) in names
        assert (2, {'name': 'Bob'}) in names

    def test_delete_tuple(self, setup_storage):
        # 1. Create and Insert
        table_name = "tasks"
        columns = [
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("title", DataTypes.STR, None)
        ]
        self.table_manager.create_table(CreateTableExp(table_name, columns))

        self.page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 1), InsertValueExp("title", "Task1")]))
        self.page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 2), InsertValueExp("title", "Task2")]))
        self.page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 3), InsertValueExp("title", "Task3")]))

        # 2. Delete Tuple 2
        self.page_manager.delete_tuple(table_name, 2)

        # 3. Verify Scan
        # Should only get 1 and 3
        # Scan both columns and combine results
        results = []
        id_data = {}
        title_data = {}

        for page in self.page_manager.scan_column(table_name, "id"):
            for rid, val in page.page_data:
                if rid not in page.page_rids_deleted:
                    id_data[rid] = val

        for page in self.page_manager.scan_column(table_name, "title"):
            for rid, val in page.page_data:
                if rid not in page.page_rids_deleted:
                    title_data[rid] = val

        for rid in id_data:
            if rid in title_data:
                results.append((rid, {'id': id_data[rid], 'title': title_data[rid]}))

        assert len(results) == 2
        rids = [r[0] for r in results]
        assert 1 in rids
        assert 3 in rids
        assert 2 not in rids
        
        # Verify data
        for rid, record in results:
            if rid == 1:
                assert record['title'] == 'Task1'
            elif rid == 3:
                assert record['title'] == 'Task3'

        # 4. Verify Persistence (Optional check of underlying file or re-read)
        # We can force a fresh read by creating a new PageManager or checking the file content if we want,
        # but the scan test covers the logic.
