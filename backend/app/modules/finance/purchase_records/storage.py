"""
Purchase Records File Storage

Handles screenshot file storage on the local filesystem.
Database only stores metadata; binaries are kept on disk.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

UPLOAD_ROOT = Path("runtime_data/uploads/finance/purchase_records")


def _ensure_upload_dir() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def save_screenshot(*, file: UploadFile) -> tuple[str, str, str, int]:
    """Save an uploaded screenshot and return metadata.

    Returns:
        (relative_path, original_name, mime_type, size)
    """
    upload_dir = _ensure_upload_dir()
    original_name = file.filename or "unknown"
    extension = Path(original_name).suffix or ".bin"
    storage_name = f"{uuid.uuid4().hex}{extension}"
    storage_path = upload_dir / storage_name

    with storage_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size = storage_path.stat().st_size
    relative_path = f"finance/purchase_records/{storage_name}"
    mime_type = file.content_type or "application/octet-stream"
    return relative_path, original_name, mime_type, size


def delete_screenshot(*, relative_path: str) -> None:
    """Delete a screenshot file from disk."""
    # relative_path is like "finance/purchase_records/<uuid>.png"
    file_path = Path("runtime_data/uploads") / relative_path
    if file_path.exists():
        file_path.unlink()


def get_screenshot_path(*, relative_path: str) -> Path:
    """Resolve a screenshot relative path to an absolute Path."""
    return Path("runtime_data/uploads") / relative_path
