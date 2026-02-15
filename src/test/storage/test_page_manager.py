import os
import shutil
import pytest


from src.parser.ast_schema import CreateTableExp, CreateTableColumExp, InsertExp, InsertValueExp, DataTypes
from src.storage.page_manager import PageManager
from src.storage.table_manager import TableManager
from src.storage.metadata import MetadataController
from src.storage.constant import STORAGE_PATH
from src.errors import NoColumnFoundError

@pytest.fixture
def clean_storage():
    if os.path.exists(STORAGE_PATH):
        shutil.rmtree(STORAGE_PATH)
    yield
    if os.path.exists(STORAGE_PATH):
        shutil.rmtree(STORAGE_PATH)

@pytest.fixture
def managers(clean_storage):
    metadata = MetadataController()
    metadata.init_file()
    table_manager = TableManager(metadata)
    page_manager = PageManager(metadata, table_manager)
    return page_manager, table_manager

def test_get_tuple(managers):
    page_manager, table_manager = managers
    table_name = "test_get"
    
    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
    )
    table_manager.create_table(create_exp)
    
    insert_exp = InsertExp(
        table_name=table_name,
        values_map=[
            InsertValueExp("id", 1),
            InsertValueExp("name", "Alice")
        ]
    )
    page_manager.write_tuple(insert_exp)
    
    result = page_manager.get(table_name, 1)
    
    assert result is not None
    assert result["id"] == 1
    assert result["name"] == "Alice"

def test_update_tuple(managers):
    page_manager, table_manager = managers
    table_name = "test_update"
    
    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
    )
    table_manager.create_table(create_exp)
    
    insert_exp = InsertExp(
        table_name=table_name,
        values_map=[InsertValueExp("id", 1), InsertValueExp("name", "Alice")]
    )
    page_manager.write_tuple(insert_exp)
    
    assert page_manager.get(table_name, 1)["name"] == "Alice"
    
    # OLAP-style update: returns new row_id, old row_id is tombstoned
    new_row_id = page_manager.update(table_name, 1, {"id": 1, "name": "Bob"})

    assert new_row_id is not None
    assert new_row_id == 2  # New row_id assigned

    # Old row_id should be tombstoned (not found)
    assert page_manager.get(table_name, 1) is None

    # New data at new row_id
    updated_result = page_manager.get(table_name, new_row_id)
    assert updated_result is not None
    assert updated_result["name"] == "Bob"
    assert updated_result["id"] == 1

def test_multiple_updates(managers):
    page_manager, table_manager = managers
    table_name = "test_multi"
    
    create_exp = CreateTableExp(table_name=table_name, table_columns=[CreateTableColumExp("val", DataTypes.INT, None)])
    table_manager.create_table(create_exp)
    
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("val", 10)]))
    
    # First update: row_id 1 -> row_id 2
    new_row_id = page_manager.update(table_name, 1, {"val": 20})
    assert new_row_id == 2
    assert page_manager.get(table_name, 1) is None  # Old tombstoned
    assert page_manager.get(table_name, new_row_id)["val"] == 20

    # Second update: row_id 2 -> row_id 3
    new_row_id = page_manager.update(table_name, new_row_id, {"val": 30})
    assert new_row_id == 3
    assert page_manager.get(table_name, 2) is None  # Old tombstoned
    assert page_manager.get(table_name, new_row_id)["val"] == 30

def test_get_deleted_tuple(managers):
    page_manager, table_manager = managers
    table_name = "test_del"
    
    create_exp = CreateTableExp(table_name=table_name, table_columns=[CreateTableColumExp("id", DataTypes.INT, None)])
    table_manager.create_table(create_exp)
    
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 1)]))
    page_manager.delete_tuple(table_name, 1)
    
    result = page_manager.get(table_name, 1)
    assert result is None

def test_update_missing(managers):
    page_manager, table_manager = managers
    table_name = "test_missing"
    create_exp = CreateTableExp(table_name=table_name, table_columns=[CreateTableColumExp("id", DataTypes.INT, None)])
    table_manager.create_table(create_exp)
    
    assert page_manager.update(table_name, 999, {"id": 999}) is None


# ==========================================
# Projection-aware read tests
# ==========================================

def test_get_with_column_projection(managers):
    """Test get() with specific columns (projection-aware read)."""
    page_manager, table_manager = managers
    table_name = "test_projection"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None),
            CreateTableColumExp("age", DataTypes.INT, None)
        ]
    )
    table_manager.create_table(create_exp)

    insert_exp = InsertExp(
        table_name=table_name,
        values_map=[
            InsertValueExp("id", 1),
            InsertValueExp("name", "Alice"),
            InsertValueExp("age", 30)
        ]
    )
    page_manager.write_tuple(insert_exp)

    # Get only 'name' column
    result = page_manager.get(table_name, 1, columns=["name"])
    assert result is not None
    assert result == {"name": "Alice"}
    assert "id" not in result
    assert "age" not in result


def test_get_with_multiple_column_projection(managers):
    """Test get() with multiple specific columns."""
    page_manager, table_manager = managers
    table_name = "test_multi_proj"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None),
            CreateTableColumExp("age", DataTypes.INT, None)
        ]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [
        InsertValueExp("id", 1),
        InsertValueExp("name", "Bob"),
        InsertValueExp("age", 25)
    ]))

    # Get 'id' and 'age' columns only
    result = page_manager.get(table_name, 1, columns=["id", "age"])
    assert result is not None
    assert result == {"id": 1, "age": 25}
    assert "name" not in result


def test_get_all_columns_when_none_specified(managers):
    """Test get() returns all columns when columns=None (default behavior)."""
    page_manager, table_manager = managers
    table_name = "test_all_cols"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [
        InsertValueExp("id", 1),
        InsertValueExp("name", "Charlie")
    ]))

    # Get all columns (default)
    result = page_manager.get(table_name, 1)
    assert result is not None
    assert result == {"id": 1, "name": "Charlie"}


def test_get_columns_method(managers):
    """Test get_columns() explicit projection method."""
    page_manager, table_manager = managers
    table_name = "test_get_cols"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("a", DataTypes.INT, None),
            CreateTableColumExp("b", DataTypes.STR, None),
            CreateTableColumExp("c", DataTypes.INT, None)
        ]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [
        InsertValueExp("a", 10),
        InsertValueExp("b", "test"),
        InsertValueExp("c", 20)
    ]))

    result = page_manager.get_columns(table_name, 1, ["b"])
    assert result == {"b": "test"}


def test_get_columns_empty_list_raises_error(managers):
    """Test get_columns() raises error for empty column list."""
    page_manager, table_manager = managers
    table_name = "test_empty_cols"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[CreateTableColumExp("id", DataTypes.INT, None)]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 1)]))

    with pytest.raises(NoColumnFoundError):
        page_manager.get_columns(table_name, 1, [])


# ==========================================
# Scan API tests
# ==========================================

def test_scan_returns_all_rows(managers):
    """Test scan() returns all non-deleted rows."""
    page_manager, table_manager = managers
    table_name = "test_scan_all"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("id", DataTypes.INT, None),
            CreateTableColumExp("name", DataTypes.STR, None)
        ]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 1), InsertValueExp("name", "Alice")]))
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 2), InsertValueExp("name", "Bob")]))
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("id", 3), InsertValueExp("name", "Charlie")]))

    results = list(page_manager.scan(table_name))

    assert len(results) == 3
    assert (1, {"id": 1, "name": "Alice"}) in results
    assert (2, {"id": 2, "name": "Bob"}) in results
    assert (3, {"id": 3, "name": "Charlie"}) in results


def test_scan_excludes_deleted_rows(managers):
    """Test scan() excludes tombstoned rows."""
    page_manager, table_manager = managers
    table_name = "test_scan_del"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[CreateTableColumExp("val", DataTypes.INT, None)]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("val", 10)]))
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("val", 20)]))
    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("val", 30)]))

    page_manager.delete_tuple(table_name, 2)

    results = list(page_manager.scan(table_name))

    assert len(results) == 2
    rids = [r[0] for r in results]
    assert 1 in rids
    assert 2 not in rids  # Deleted
    assert 3 in rids


def test_scan_with_projection(managers):
    """Test scan() with column projection."""
    page_manager, table_manager = managers
    table_name = "test_scan_proj"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[
            CreateTableColumExp("a", DataTypes.INT, None),
            CreateTableColumExp("b", DataTypes.STR, None),
            CreateTableColumExp("c", DataTypes.INT, None)
        ]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [
        InsertValueExp("a", 1),
        InsertValueExp("b", "test"),
        InsertValueExp("c", 100)
    ]))

    # Scan with projection - only columns a and c
    results = list(page_manager.scan(table_name, columns=["a", "c"]))

    assert len(results) == 1
    row_id, record = results[0]
    assert row_id == 1
    assert record == {"a": 1, "c": 100}
    assert "b" not in record


def test_scan_empty_table(managers):
    """Test scan() on empty table returns no results."""
    page_manager, table_manager = managers
    table_name = "test_scan_empty"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[CreateTableColumExp("id", DataTypes.INT, None)]
    )
    table_manager.create_table(create_exp)

    results = list(page_manager.scan(table_name))
    assert len(results) == 0


def test_scan_after_updates(managers):
    """Test scan() correctly shows updated data with new row_ids."""
    page_manager, table_manager = managers
    table_name = "test_scan_upd"

    create_exp = CreateTableExp(
        table_name=table_name,
        table_columns=[CreateTableColumExp("val", DataTypes.INT, None)]
    )
    table_manager.create_table(create_exp)

    page_manager.write_tuple(InsertExp(table_name, [InsertValueExp("val", 100)]))

    # Update creates new row_id, tombstones old
    new_rid = page_manager.update(table_name, 1, {"val": 200})

    results = list(page_manager.scan(table_name))

    assert len(results) == 1
    row_id, record = results[0]
    assert row_id == new_rid  # New row_id from update
    assert record["val"] == 200
