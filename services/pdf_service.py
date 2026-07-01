# services/pdf_service.py
"""Extract plain text from a PDF file's raw bytes.

Primary engine is PyMuPDF (fitz), which reconstructs words from glyph
positions well — important for resumes exported by design tools (Canva/Figma)
that place each character individually. pypdf is kept as a fallback for the
rare file MuPDF can't open.
"""

import io

import fitz  # PyMuPDF
from pypdf import PdfReader


def _extract_with_fitz(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        return "\n".join(page.get_text("text") for page in doc).strip()
    finally:
        doc.close()


def _extract_with_pypdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def extract_pdf_text(data: bytes) -> str:
    """
    Return the concatenated text of every page in the PDF.

    Returns an empty string when nothing can be extracted (corrupt file, or a
    scanned/image-only PDF with no embedded text layer). Callers treat an empty
    or too-short result as "unsupported".
    """
    try:
        text = _extract_with_fitz(data)
        if text:
            return text
    except Exception as e:
        print(f"[pdf] fitz extraction failed: {type(e).__name__}: {e}")

    try:
        return _extract_with_pypdf(data)
    except Exception as e:
        print(f"[pdf] pypdf extraction failed: {type(e).__name__}: {e}")
        return ""
