"""
Equipment Purchase Contract Filler Storage

Handles the built-in contract template file and generated DOCX outputs.
"""

import shutil
import uuid
from pathlib import Path

TEMPLATE_SOURCE = Path(__file__).parent / "template.docx"
UPLOAD_ROOT = Path("runtime_data/uploads")
TEMPLATE_DIR = UPLOAD_ROOT / "contracts/equipment_purchase_filler/template"
FILLED_DIR = UPLOAD_ROOT / "contracts/equipment_purchase_filler/filled"
TEMPLATE_FILENAME = "设备购销合同20250607(Revised)(None)可编辑.docx"


def ensure_template() -> Path:
    """Ensure the built-in contract template exists in the runtime upload dir."""
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    dest = TEMPLATE_DIR / TEMPLATE_FILENAME
    if not dest.exists() and TEMPLATE_SOURCE.exists():
        shutil.copy2(TEMPLATE_SOURCE, dest)
    return dest


def get_template_path() -> Path:
    """Return the path to the built-in template file."""
    path = ensure_template()
    if not path.exists():
        raise FileNotFoundError("Equipment purchase contract template file not found")
    return path


def ensure_filled_dir() -> Path:
    """Ensure the filled output directory exists."""
    FILLED_DIR.mkdir(parents=True, exist_ok=True)
    return FILLED_DIR


def save_filled_docx(*, source_path: Path, version_id: uuid.UUID, filename: str) -> tuple[str, int]:
    """Save a generated DOCX to the filled output directory.

    Returns (relative_path, file_size).
    """
    upload_dir = ensure_filled_dir()
    safe_name = Path(filename).name
    stored_name = f"{version_id}_{safe_name}"
    dest = upload_dir / stored_name

    shutil.copy2(source_path, dest)
    size = dest.stat().st_size
    relative_path = f"contracts/equipment_purchase_filler/filled/{stored_name}"
    return relative_path, size


def get_filled_path(*, relative_path: str) -> Path:
    """Resolve a relative filled file path to an absolute path."""
    return UPLOAD_ROOT / relative_path


def delete_filled_docx(*, relative_path: str | None) -> None:
    """Delete a generated DOCX file if it exists."""
    if not relative_path:
        return
    path = get_filled_path(relative_path=relative_path)
    if path.exists():
        path.unlink()
