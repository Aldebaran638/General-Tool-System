"""
Reimbursement Exports Storage

File storage utilities for exported Excel files.
"""

from pathlib import Path

from .constants import EXPORT_DIR


def _resolve_export_dir() -> Path:
    export_dir = Path(EXPORT_DIR)
    if not export_dir.is_absolute():
        project_root = Path(__file__).resolve().parents[5]
        export_dir = (project_root / export_dir).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


EXPORT_DIR_PATH = _resolve_export_dir()


def save_excel(*, data: bytes, filename: str) -> tuple[str, int]:
    """Save Excel bytes to disk and return (absolute_path, size)."""
    file_path = EXPORT_DIR_PATH / filename
    file_path.write_bytes(data)
    return str(file_path), file_path.stat().st_size


def delete_excel(*, file_path: str) -> None:
    """Delete an Excel file from disk."""
    Path(file_path).unlink(missing_ok=True)
