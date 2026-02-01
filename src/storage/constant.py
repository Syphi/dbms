import os
from pathlib import Path

VERSION = "0.1"

# Get the project root directory (parent of src/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Storage paths relative to project root
STORAGE_PATH = str(_PROJECT_ROOT / "storage")
METADATA_PATH = str(_PROJECT_ROOT / "storage" / "metadata.txt")
TABLES_STORAGE_PATH = str(_PROJECT_ROOT / "storage" / "table")
