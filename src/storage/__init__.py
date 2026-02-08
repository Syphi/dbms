from src.storage.metadata import MetadataController
from src.storage.table_manager import TableManager
from src.storage.page_manager import PageManager


metadata_controller = MetadataController()
table_manager = TableManager(metadata_controller=metadata_controller)
page_manager = PageManager(metadata_controller=metadata_controller, table_manager=table_manager)
