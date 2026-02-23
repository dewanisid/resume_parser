"""
PDFExtractor — pulls raw text out of a PDF file.

Strategy:
1. Try pdfplumber (fast, accurate for digitally-created PDFs).
2. If the extracted text is sparse (< 100 chars/page on average), the PDF
   is likely a scanned image. Fall back to Tesseract OCR.
3. If both methods fail, raise PDFExtractionError.
"""
import logging
from pathlib import Path
from typing import Dict, Any

import pdfplumber

logger = logging.getLogger("apps.parser")

# If the average extracted characters per page is below this threshold,
# we treat the PDF as a scanned image and switch to OCR.
TEXT_DENSITY_THRESHOLD = 100


class PDFExtractionError(Exception):
    pass


class PDFExtractor:

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point. Tries pdfplumber first, falls back to OCR.

        Returns:
            {
                "text": str,           — the full extracted text
                "pages": int,          — number of pages in the PDF
                "method": str,         — "pdfplumber" or "ocr"
                "confidence": float,   — rough 0.0–1.0 quality signal
            }

        Raises:
            PDFExtractionError if all methods fail.
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFExtractionError(f"File not found: {file_path}")

        logger.info("Starting PDF extraction for: %s", path.name)

        # --- Attempt 1: pdfplumber ---
        try:
            result = self._extract_with_pdfplumber(str(path))
            avg_density = len(result["text"]) / max(result["pages"], 1)

            if avg_density >= TEXT_DENSITY_THRESHOLD:
                logger.info(
                    "pdfplumber succeeded — %d chars across %d pages",
                    len(result["text"]), result["pages"],
                )
                return {
                    "text": result["text"],
                    "pages": result["pages"],
                    "method": "pdfplumber",
                    # Soft cap: 500+ chars/page is considered full confidence
                    "confidence": min(1.0, avg_density / 500),
                }

            logger.info(
                "Low text density (%.1f chars/page) — falling back to OCR",
                avg_density,
            )

        except Exception as exc:
            logger.warning("pdfplumber failed: %s", exc)

        # --- Attempt 2: Tesseract OCR ---
        try:
            result = self._extract_with_ocr(str(path))
            logger.info(
                "OCR succeeded — %d chars across %d pages",
                len(result["text"]), result["pages"],
            )
            return {
                "text": result["text"],
                "pages": result["pages"],
                "method": "ocr",
                # OCR is inherently less reliable; use a fixed lower bound
                "confidence": 0.6,
            }

        except Exception as exc:
            logger.error("OCR failed: %s", exc)
            raise PDFExtractionError(
                f"All extraction methods failed for {path.name}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """Extract text using pdfplumber, preserving reading order."""
        pages_text = []
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                # x_tolerance/y_tolerance tune how aggressively nearby
                # characters are merged — these defaults work well for resumes
                text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                pages_text.append(text)

        combined = "\n\n".join(pages_text).strip()
        return {"text": combined, "pages": num_pages}

    def _extract_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """
        Convert each PDF page to a high-res image, then run Tesseract OCR.
        Lazy imports so the heavy OCR libraries are only loaded when needed.
        """
        import pytesseract
        from pdf2image import convert_from_path

        # 300 DPI gives good OCR accuracy without being too slow
        images = convert_from_path(file_path, dpi=300)
        pages_text = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="eng")
            pages_text.append(text)

        combined = "\n\n".join(pages_text).strip()
        return {"text": combined, "pages": len(images)}
