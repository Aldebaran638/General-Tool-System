"""
Storage path utilities.

Centralises all logic for resolving and validating the upload/storage
directory so that main.py, docx_generator, and download endpoints all
use the same code path.

Configuration is driven by the UPLOAD_DIR environment variable (see
app/core/config.py and .env-example).

Examples
--------
Relative path (default, resolved relative to project root):
    UPLOAD_DIR=backend/app/uploads/

Absolute path on the host (bind-mounted into the container):
    UPLOAD_DIR=/mnt/nas/exam-papers/

Docker Compose usage: add a volume to the backend service so the
container can access the directory:

    services:
      backend:
        volumes:
          - /mnt/nas/exam-papers:/mnt/nas/exam-papers
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Project root is 4 levels above app/core/storage.py:
#   storage.py → core/ → app/ → backend/ → PROJECT_ROOT
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_upload_dir() -> Path:
    """Return the absolute path of the configured upload/storage directory.

    Rules:
    - If UPLOAD_DIR is absolute, use it as-is.
    - If UPLOAD_DIR is relative, resolve it relative to the project root
      (i.e. the directory that contains ``pyproject.toml``).

    The returned path is guaranteed to be absolute but is NOT guaranteed
    to exist yet — callers that need the directory should call
    ``ensure_upload_dir()`` instead.
    """
    raw = Path(settings.UPLOAD_DIR)
    if raw.is_absolute():
        return raw
    return (_PROJECT_ROOT / raw).resolve()


def resolve_papers_dir() -> Path:
    """Return the absolute path of the ``papers/`` sub-directory inside
    the upload root.  This is where generated ``.docx`` files live.
    """
    return resolve_upload_dir() / "papers"


def ensure_upload_dir() -> Path:
    """Create the upload directory (and ``papers/`` sub-directory) if
    they don't exist yet, then return the upload root path.

    Raises ``RuntimeError`` if the directory cannot be created or is not
    writable — this surfaces as a loud startup failure rather than a
    silent permission error at generation time.
    """
    upload_root = resolve_upload_dir()
    papers_dir = upload_root / "papers"

    try:
        papers_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create upload directory {papers_dir}: {exc}\n"
            "Check that UPLOAD_DIR is correctly configured and that the "
            "process has write permission to that path."
        ) from exc

    # Write-access probe
    probe = papers_dir / ".write_probe"
    try:
        probe.touch()
        probe.unlink()
    except OSError as exc:
        raise RuntimeError(
            f"Upload directory {papers_dir} is not writable: {exc}\n"
            "Check file system permissions for UPLOAD_DIR."
        ) from exc

    logger.info("[storage] upload directory: %s", upload_root)
    return upload_root


def storage_info() -> dict:
    """Return a summary dict for diagnostics / admin endpoints."""
    upload_root = resolve_upload_dir()
    papers_dir = upload_root / "papers"
    exists = papers_dir.exists()
    writable = False
    if exists:
        probe = papers_dir / ".write_probe"
        try:
            probe.touch()
            probe.unlink()
            writable = True
        except OSError:
            pass

    # Count generated docx files
    docx_count = len(list(papers_dir.glob("*.docx"))) if exists else 0

    return {
        "upload_dir": str(upload_root),
        "papers_dir": str(papers_dir),
        "configured_value": settings.UPLOAD_DIR,
        "papers_dir_exists": exists,
        "papers_dir_writable": writable,
        "docx_file_count": docx_count,
    }
