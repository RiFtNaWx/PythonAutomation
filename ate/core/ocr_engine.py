"""OCR only when PDF text is thin. Cloud HTML first. No Qianfan 5B sidecar.

Engines: local text -> run-ic HTML (one SKU) -> PaddleOCR (autodownload) -> EasyOCR.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

THIN = 200
_SKIP = frozenset({"qianfan", "unlimited", "qianfan-ocr", "unlimited-ocr"})


def text_is_thin(blob: str) -> bool:
    return len((blob or "").strip()) < THIN


def _pip_install(*pkgs: str) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", *pkgs],
        timeout=600,
    )


def _paddle_text(path: Path) -> str:
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except ImportError:
        _pip_install("paddlepaddle", "paddleocr")
        from paddleocr import PaddleOCR  # type: ignore
    ocr = PaddleOCR(use_angle_cls=True, lang="en")
    result = ocr.ocr(str(path), cls=True)
    lines: list[str] = []
    for page in result or []:
        for row in page or []:
            if row and row[1]:
                lines.append(str(row[1][0]))
    return "\n".join(lines)


def _easy_text(path: Path) -> str:
    try:
        import easyocr  # type: ignore
    except ImportError:
        _pip_install("easyocr")
        import easyocr  # type: ignore
    reader = easyocr.Reader(["en"])
    rows = reader.readtext(str(path))
    return "\n".join(str(r[1]) for r in rows)


def extract_pdf(
    path: Path,
    *,
    engine: str = "auto",
    named_cloud: bool = False,
) -> dict[str, Any]:
    """Return {engine, text, thin}. Never writes yaml. Never dumps into #Test_Database."""
    from ate.core.lookup import _pdf_plain

    pdf = Path(path)
    if not pdf.is_file():
        raise FileNotFoundError(f"missing pdf: {pdf}")
    want = str(engine or "auto").strip().lower()
    if want in _SKIP and not named_cloud:
        raise ValueError(
            "Qianfan-OCR / Unlimited-OCR need a named confirm. Use auto|text|paddle|easyocr."
        )
    if want in _SKIP:
        raise ValueError(
            "Named cloud OCR is parked on this laptop (5B / long-horizon). Use paddle or easyocr."
        )
    plain = _pdf_plain(pdf)
    if want == "text" or (want == "auto" and not text_is_thin(plain)):
        return {"engine": "text", "text": plain, "thin": text_is_thin(plain)}
    if want in ("paddle", "auto"):
        try:
            blob = _paddle_text(pdf)
            return {"engine": "paddle", "text": blob, "thin": text_is_thin(blob)}
        except Exception as exc:
            if want == "paddle":
                raise RuntimeError(f"paddleocr failed: {exc}") from exc
            last = exc
        try:
            blob = _easy_text(pdf)
            return {"engine": "easyocr", "text": blob, "thin": text_is_thin(blob)}
        except Exception as exc:
            raise RuntimeError(f"text thin; paddle={last}; easyocr={exc}") from exc
    if want == "easyocr":
        blob = _easy_text(pdf)
        return {"engine": "easyocr", "text": blob, "thin": text_is_thin(blob)}
    return {"engine": "text", "text": plain, "thin": text_is_thin(plain)}
