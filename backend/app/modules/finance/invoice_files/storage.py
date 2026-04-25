"""
Invoice File Storage

Handles PDF file storage on the local filesystem.
Database only stores metadata; binaries are kept on disk.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_ROOT = Path("runtime_data/uploads/finance/invoice_files")
VALID_PDF_MIME_TYPES = {"application/pdf"}
VALID_PDF_EXTENSIONS = {".pdf"}


def _ensure_upload_dir() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def validate_pdf_file(*, file: UploadFile) -> None:
    """Validate that the uploaded file is a PDF.

    Raises HTTPException(422) if MIME type or extension is invalid.
    """
    original_name = file.filename or "unknown"
    extension = Path(original_name).suffix.lower()
    mime_type = file.content_type or "application/octet-stream"

    if mime_type not in VALID_PDF_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid PDF MIME type: {mime_type}",
        )
    if extension not in VALID_PDF_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid PDF extension: {extension}",
        )


def save_pdf(*, file: UploadFile) -> tuple[str, str, str, int]:
    """Save an uploaded PDF and return metadata.

    Returns:
        (relative_path, original_name, mime_type, size)
    """
    validate_pdf_file(file=file)

    upload_dir = _ensure_upload_dir()
    original_name = file.filename or "unknown.pdf"
    extension = Path(original_name).suffix or ".pdf"
    storage_name = f"{uuid.uuid4().hex}{extension}"
    storage_path = upload_dir / storage_name

    with storage_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size = storage_path.stat().st_size
    relative_path = f"finance/invoice_files/{storage_name}"
    mime_type = file.content_type or "application/pdf"
    return relative_path, original_name, mime_type, size


def delete_pdf(*, relative_path: str) -> None:
    """Delete a PDF file from disk."""
    file_path = Path("runtime_data/uploads") / relative_path
    if file_path.exists():
        file_path.unlink()


def get_pdf_path(*, relative_path: str) -> Path:
    """Resolve a PDF relative path to an absolute Path."""
    return Path("runtime_data/uploads") / relative_path
