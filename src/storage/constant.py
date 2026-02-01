from pathlib import Path

VERSION = "0.1"

_PROJECT_ROOT = Path(__file__).parent.parent.parent

STORAGE_PATH = str(_PROJECT_ROOT / "storage")
METADATA_PATH = str(_PROJECT_ROOT / "storage" / "metadata.txt")
TABLES_STORAGE_PATH = str(_PROJECT_ROOT / "storage" / "table")
