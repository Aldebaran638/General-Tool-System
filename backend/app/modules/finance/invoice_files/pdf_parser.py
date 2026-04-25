"""
PDF Parse Preview Adapter

Provides PDF-based form prefill for invoice files.
- Uses PyMuPDF for text extraction first.
- Falls back to PaddleOCR local pretrained model when text is empty
  and local OCR is enabled and available.
- Does NOT persist files or database records.
- Respects global settings for OCR behavior.
"""

import logging
import re
import tempfile
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.core.config import settings

from .models import ParsePreviewResponse

logger = logging.getLogger(__name__)

_paddleocr = None

_REQUIRED_MODEL_SUBDIRS = ("det", "rec", "cls")


def _has_required_local_models(model_dir: Path) -> bool:
    """Check that det/rec/cls subdirectories exist and are non-empty."""
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
    """Lazy-init PaddleOCR respecting settings."""
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


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf_path))
        texts: list[str] = []
        for page in doc:
            text = page.get_text()
            if text:
                texts.append(text)
        doc.close()
        return "\n".join(texts)
    except Exception as exc:
        logger.warning("PyMuPDF text extraction failed: %s", exc)
        return ""


def _render_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 200) -> Path | None:
    """Render a PDF page to a temporary image."""
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        if page_num >= len(doc):
            doc.close()
            return None
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        tmp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = Path(tmp_image.name)
        pix.save(str(tmp_path))
        doc.close()
        return tmp_path
    except Exception as exc:
        logger.warning("PDF page render failed: %s", exc)
        return None


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


def _parse_invoice_number(text: str) -> str | None:
    """Heuristic: try to find invoice number."""
    # Common Chinese invoice number patterns
    patterns = [
        r"发票号码?[:：\s]*([A-Za-z0-9]{8,20})",
        r"发票代码?[:：\s]*([A-Za-z0-9]{10,12})",
        r"No\.?[:：\s]*([A-Za-z0-9]{8,20})",
        r"号码?[:：\s]*([A-Za-z0-9]{8,20})",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(1)
    return None


def _parse_date(text: str) -> str | None:
    """Heuristic: try to find a date-like string YYYY-MM-DD."""
    match = re.search(r"(\d{4}[\-/]\d{2}[\-/]\d{2})", text)
    if match:
        return match.group(1).replace("/", "-")
    return None


def _parse_amount(text: str) -> str | None:
    """Heuristic: try to find an amount-like number."""
    # Look for total amount patterns
    patterns = [
        r"(?:合计金额|总金额|价税合计|小写)[:：\s]*(?:¥|￥|\\$)?\s*([\d,]+\.\d{2})",
        r"(?:金额|总价)[:：\s]*(?:¥|￥|\\$)?\s*([\d,]+\.\d{2})",
        r"(?:¥|￥|\\$)\s*([\d,]+\.\d{2})",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(1).replace(",", "")
    # Fallback: any decimal number with 2 places
    match = re.search(r"([\d,]+\.\d{2})", text)
    if match:
        return match.group(1).replace(",", "")
    return None


def _parse_tax_amount(text: str) -> str | None:
    """Heuristic: try to find tax amount."""
    patterns = [
        r"(?:税额|税金|税)[:：\s]*(?:¥|￥|\\$)?\s*([\d,]+\.\d{2})",
        r"(?:税率|税)[:：\s]*\d+%?",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            val = match.group(1).replace(",", "") if match.lastindex else None
            if val:
                return val
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


def _parse_buyer_seller(text: str) -> tuple[str | None, str | None]:
    """Heuristic: try to find buyer and seller names."""
    buyer: str | None = None
    seller: str | None = None

    buyer_match = re.search(r"(?:购买方|买方|购方)[:：\s]*\n?([^\n]{2,50})", text)
    if buyer_match:
        buyer = buyer_match.group(1).strip()

    seller_match = re.search(r"(?:销售方|卖方|销方)[:：\s]*\n?([^\n]{2,50})", text)
    if seller_match:
        seller = seller_match.group(1).strip()

    return buyer, seller


def _parse_invoice_type(text: str) -> str | None:
    """Heuristic: try to detect invoice type."""
    if "增值税专用发票" in text:
        return "vat_special_invoice"
    if "普通发票" in text or "增值税普通发票" in text:
        return "general_invoice"
    if "通行费" in text or "高速" in text:
        return "toll_invoice"
    return None


def _build_preview(text: str) -> ParsePreviewResponse:
    """Build preview from extracted text."""
    buyer, seller = _parse_buyer_seller(text)
    return ParsePreviewResponse(
        invoice_number=_parse_invoice_number(text),
        invoice_date=_parse_date(text),
        invoice_amount=_parse_amount(text),
        tax_amount=_parse_tax_amount(text),
        currency=_parse_currency(text),
        buyer=buyer,
        seller=seller,
        invoice_type=_parse_invoice_type(text),
        note=None,
    )


def run_parse_preview(*, file: UploadFile) -> ParsePreviewResponse:
    """Run PDF parse on an uploaded file and return prefill data.

    This function does NOT save the file to the permanent upload directory.
    It writes to a temporary location, extracts text, then cleans up.
    """
    suffix = Path(file.filename or "invoice.pdf").suffix
    if not suffix:
        suffix = ".pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        try:
            file.file.seek(0)
            tmp.write(file.file.read())
            tmp.flush()

            text = _extract_text_from_pdf(tmp_path)

            if not text.strip():
                # Try OCR fallback if text extraction is empty
                if _init_paddleocr():
                    image_path = _render_page_to_image(tmp_path)
                    if image_path is not None:
                        try:
                            text = _extract_text_from_image(image_path)
                        finally:
                            if image_path.exists():
                                image_path.unlink()

            return _build_preview(text)
        except Exception as exc:
            logger.warning("PDF parse preview failed: %s", exc)
            return ParsePreviewResponse()
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
