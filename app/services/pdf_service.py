from pathlib import Path

from fastapi import HTTPException
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Reads a PDF and returns its concatenated text.
    Raises a clean HTTP error instead of a raw traceback if the file
    is missing, corrupted, or has no extractable text (e.g. a scanned
    image PDF with no OCR layer).
    """
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found.")

    try:
        reader = PdfReader(file_path)
    except PdfReadError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF.")

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from this PDF. It may be a scanned image without OCR.",
        )

    return text
