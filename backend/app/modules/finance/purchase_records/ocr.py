"""
OCR Preview Adapter

Provides OCR-based form prefill for purchase record screenshots.
- Uses PaddleOCR local pretrained model when available and enabled.
- Falls back gracefully with a clear error if dependencies are missing or disabled.
- Does NOT persist files or database records.
- Respects global settings for OCR behavior.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings

from .models import OCRPreviewResponse

logger = logging.getLogger(__name__)

# Attempt to import PaddleOCR; if unavailable, keep _paddleocr as None.
_paddleocr = None


_REQUIRED_MODEL_SUBDIRS = ("det", "rec", "cls")


def _has_required_local_models(model_dir: Path) -> bool:
    """Check that det/rec/cls subdirectories exist and are non-empty.

    Returns True only when every required subdirectory exists and contains
    at least one file. This is used when OCR_ALLOW_MODEL_DOWNLOAD=false to
    avoid triggering any model download.
    """
    if not model_dir.exists() or not model_dir.is_dir():
        return False
    for sub in _REQUIRED_MODEL_SUBDIRS:
        sub_path = model_dir / sub
        if not sub_path.exists() or not sub_path.is_dir():
            logger.warning("Missing model subdirectory: %s", sub_path)
            return False
        if not any(sub_path.iterdir()):
            logger.warning("Empty model subdirectory: %s", sub_path)
            return False
    return True


def _init_paddleocr() -> bool:
    """Lazy-init PaddleOCR respecting settings.

    When OCR_ALLOW_MODEL_DOWNLOAD is false, the OCR_MODEL_DIR must exist
    and contain det/rec/cls model files; otherwise we degrade to empty preview.
    """
    global _paddleocr
    if _paddleocr is not None:
        return True

    if not settings.ENABLE_LOCAL_OCR:
        logger.info("ENABLE_LOCAL_OCR is disabled; skipping PaddleOCR init")
        return False
    if settings.OCR_PROVIDER != "paddleocr":
        logger.info("OCR_PROVIDER is not paddleocr; skipping PaddleOCR init")
        return False

    model_dir = Path(settings.OCR_MODEL_DIR)
    if not settings.OCR_ALLOW_MODEL_DOWNLOAD:
        if not _has_required_local_models(model_dir):
            logger.warning(
                "OCR_ALLOW_MODEL_DOWNLOAD=false and required local models not found in %s; degrading OCR",
                model_dir,
            )
            return False

    try:
        from paddleocr import PaddleOCR  # type: ignore

        # Point PaddleOCR to the local model directories.
        # PaddleOCR parameter compatibility varies by version.
        # We pass the directory for detection, recognition and classification models.
        init_kwargs: dict[str, Any] = {
            "use_angle_cls": True,
            "lang": "ch",
            "show_log": False,
        }
        if model_dir.exists():
            init_kwargs["det_model_dir"] = str(model_dir / "det")
            init_kwargs["rec_model_dir"] = str(model_dir / "rec")
            init_kwargs["cls_model_dir"] = str(model_dir / "cls")

        _paddleocr = PaddleOCR(**init_kwargs)
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("PaddleOCR initialization failed: %s", exc)
        return False


def _extract_text_from_image(image_path: Path) -> str:
    """Run OCR on an image file and return concatenated text."""
    if _paddleocr is None:
        raise RuntimeError("PaddleOCR is not available")

    result = _paddleocr.ocr(str(image_path), cls=True)
    lines: list[str] = []
    if result and result[0]:
        for line in result[0]:
            if line:
                text = line[1][0] if isinstance(line[1], tuple) else str(line[1])
                lines.append(text)
    return "\n".join(lines)


def _parse_purchase_date(text: str) -> str | None:
    """Heuristic: try to find a date-like string YYYY-MM-DD."""
    import re

    match = re.search(r"(\d{4}[\-/]\d{2}[\-/]\d{2})", text)
    if match:
        return match.group(1).replace("/", "-")
    return None


def _parse_amount(text: str) -> str | None:
    """Heuristic: try to find an amount-like number."""
    import re

    # Look for currency symbols or amounts with 2 decimal places
    match = re.search(r"(?:￥|¥|\\$|€|£)?\s*(\d{1,}(?:,\d{3})*\.\d{2})", text)
    if match:
        return match.group(1).replace(",", "")
    # Fallback: any decimal number
    match = re.search(r"(\d+\.\d{2})", text)
    if match:
        return match.group(1)
    return None


def _parse_currency(text: str) -> str | None:
    """Heuristic: detect currency from symbols or context."""
    if "￥" in text or "¥" in text or "CNY" in text or "人民币" in text:
        return "CNY"
    if "USD" in text or "$" in text:
        return "USD"
    if "EUR" in text or "€" in text:
        return "EUR"
    if "JPY" in text or "円" in text:
        return "JPY"
    if "GBP" in text or "£" in text:
        return "GBP"
    return None


def _parse_order_name(text: str) -> str | None:
    """Heuristic: first non-empty, non-date, non-amount line as order name."""
    import re

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip pure dates and amounts
        if re.match(r"^\d{4}[\-/]\d{2}[\-/]\d{2}$", line):
            continue
        if re.match(r"^\d+\.\d{2}$", line):
            continue
        if len(line) > 2:
            return line[:255]
    return None


def run_ocr_preview(*, file: UploadFile) -> OCRPreviewResponse:
    """Run OCR on an uploaded screenshot and return prefill data.

    This function does NOT save the file to the permanent upload directory.
    It writes to a temporary location, runs OCR, then cleans up.
    """
    if not _init_paddleocr():
        # Graceful degradation: return empty preview when OCR is disabled/unavailable
        return OCRPreviewResponse()

    import tempfile

    suffix = Path(file.filename or "screenshot.png").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        try:
            file.file.seek(0)
            tmp.write(file.file.read())
            tmp.flush()

            text = _extract_text_from_image(tmp_path)
            return OCRPreviewResponse(
                purchase_date=_parse_purchase_date(text),
                amount=_parse_amount(text),
                currency=_parse_currency(text),
                order_name=_parse_order_name(text),
                category=None,
                subcategory=None,
                note=None,
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
