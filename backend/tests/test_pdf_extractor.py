"""
Unit tests for PDFExtractor.

All file I/O and library calls are mocked — no real PDFs needed.
"""
import pytest
from unittest.mock import patch
from apps.parser.pdf_extractor import PDFExtractor, PDFExtractionError


@pytest.fixture
def extractor():
    return PDFExtractor()


def test_uses_pdfplumber_when_text_is_dense(tmp_path, extractor):
    """High-density text (> threshold) → pdfplumber result is returned."""
    # 600 chars / 1 page = 600 chars/page, well above the 100-char threshold
    dense_text = "A" * 600
    fake_pdf = tmp_path / "resume.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4")

    with patch.object(extractor, "_extract_with_pdfplumber",
                      return_value={"text": dense_text, "pages": 1}) as mock_pdf:
        result = extractor.extract_text(str(fake_pdf))

    assert result["method"] == "pdfplumber"
    assert result["text"] == dense_text
    assert result["pages"] == 1
    mock_pdf.assert_called_once()


def test_falls_back_to_ocr_when_text_is_sparse(tmp_path, extractor):
    """Sparse text (< threshold) triggers OCR fallback."""
    sparse_text = "A" * 50  # 50 chars / 1 page = below threshold
    ocr_text = "John Doe\nSoftware Engineer\nGoogle"
    fake_pdf = tmp_path / "scanned.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4")

    with patch.object(extractor, "_extract_with_pdfplumber",
                      return_value={"text": sparse_text, "pages": 1}):
        with patch.object(extractor, "_extract_with_ocr",
                          return_value={"text": ocr_text, "pages": 1}) as mock_ocr:
            result = extractor.extract_text(str(fake_pdf))

    assert result["method"] == "ocr"
    assert result["text"] == ocr_text
    mock_ocr.assert_called_once()


def test_falls_back_to_ocr_when_pdfplumber_raises(tmp_path, extractor):
    """If pdfplumber raises any exception, OCR is tried automatically."""
    ocr_text = "Jane Smith\nProduct Manager"
    fake_pdf = tmp_path / "corrupt.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4")

    with patch.object(extractor, "_extract_with_pdfplumber",
                      side_effect=Exception("corrupt PDF")):
        with patch.object(extractor, "_extract_with_ocr",
                          return_value={"text": ocr_text, "pages": 1}):
            result = extractor.extract_text(str(fake_pdf))

    assert result["method"] == "ocr"


def test_raises_when_file_does_not_exist(extractor):
    with pytest.raises(PDFExtractionError, match="File not found"):
        extractor.extract_text("/nonexistent/resume.pdf")


def test_raises_when_both_methods_fail(tmp_path, extractor):
    fake_pdf = tmp_path / "bad.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4")

    with patch.object(extractor, "_extract_with_pdfplumber",
                      side_effect=Exception("pdfplumber failed")):
        with patch.object(extractor, "_extract_with_ocr",
                          side_effect=Exception("ocr failed")):
            with pytest.raises(PDFExtractionError, match="All extraction methods failed"):
                extractor.extract_text(str(fake_pdf))
