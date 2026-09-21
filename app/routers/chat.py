import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import RESUME_CACHE_FILE, UPLOAD_DIR, BUNDLED_RESUME_PATH
from app.models.resume import ChatRequest, ChatResponse, Resume, ResumeStatusResponse
from app.services.chat_service import ask_candidate
from app.services.pdf_service import extract_text_from_pdf
from app.services.resume_service import get_or_parse_resume

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

RESUME_PDF_PATH = UPLOAD_DIR / "resume.pdf"


@router.post("/resume/upload", response_model=ResumeStatusResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Uploads a new resume PDF, parses it with the LLM, and caches the
    structured result. Call this once (or whenever the resume changes) -
    not on every chat message.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()
    RESUME_PDF_PATH.write_bytes(contents)

    resume_text = extract_text_from_pdf(RESUME_PDF_PATH)
    resume = get_or_parse_resume(resume_text, force_reparse=True)

    return ResumeStatusResponse(parsed=True, name=resume.name)


@router.get("/resume/status", response_model=ResumeStatusResponse)
def resume_status():
    """Lets the frontend check whether a resume has already been parsed and cached."""
    if not RESUME_CACHE_FILE.exists():
        return ResumeStatusResponse(parsed=False)

    import json

    data = json.loads(RESUME_CACHE_FILE.read_text())
    return ResumeStatusResponse(parsed=True, name=data.get("name"))


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # If someone manually uploaded a resume this session, prefer that.
    # Otherwise, fall back to the resume bundled in the repo — this
    # guarantees the assistant always has data, even right after a
    # fresh deploy or a free-tier restart that wiped uploaded files.
    pdf_path = RESUME_PDF_PATH if RESUME_PDF_PATH.exists() else BUNDLED_RESUME_PATH

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No resume is available on the server.",
        )

    resume_text = extract_text_from_pdf(pdf_path)
    resume = get_or_parse_resume(resume_text)  # uses cache, no re-parse

    answer = ask_candidate(request.question, resume)
    return ChatResponse(answer=answer)