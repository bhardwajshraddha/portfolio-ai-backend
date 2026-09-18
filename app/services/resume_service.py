import json
import logging

from fastapi import HTTPException
from groq import APIError, APIStatusError

from app.config import RESUME_CACHE_FILE
from app.models.resume import Resume
from app.services.llm_client import client, MODEL_NAME

logger = logging.getLogger(__name__)

RESUME_SCHEMA = Resume.model_json_schema()

_PARSE_SYSTEM_PROMPT = f"""
You are an expert resume parser.

Extract information from the resume based on its meaning, not only
based on exact section headings.

Different resumes may use different headings, for example:
Experience, Professional Experience, Work History, Employment, Internships.
These may all contain relevant experience.

Skills may also appear in the skills section, work experience,
internships or projects.

Return ONLY valid JSON matching this schema:
{RESUME_SCHEMA}

Rules:
1. Do not invent information.
2. If a value is not available, return null.
3. If a list has no information, return an empty list.
4. Include internships inside experiences.
5. Extract skills mentioned across the entire resume.
"""


def _parse_with_llm(resume_text: str) -> Resume:
    """Calls the LLM once to turn raw resume text into structured JSON."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _PARSE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse the following resume:\n\n{resume_text}"},
            ],
            response_format={"type": "json_object"},
        )
    except (APIError, APIStatusError) as e:
        logger.error("Groq API error while parsing resume: %s", e)
        raise HTTPException(status_code=502, detail="AI provider is currently unavailable. Please try again shortly.")

    raw_output = response.choices[0].message.content

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        logger.error("LLM returned non-JSON output: %s", raw_output)
        raise HTTPException(status_code=502, detail="Failed to parse resume data. Please try again.")

    try:
        return Resume(**data)
    except Exception:
        logger.exception("LLM JSON did not match Resume schema")
        raise HTTPException(status_code=502, detail="Resume data did not match the expected format.")


def get_or_parse_resume(resume_text: str, force_reparse: bool = False) -> Resume:
    """
    Returns the cached, already-parsed resume if it exists.
    Only calls the LLM (slow + costs money) the first time, or when
    force_reparse=True (e.g. after a new resume is uploaded).
    """
    if not force_reparse and RESUME_CACHE_FILE.exists():
        try:
            cached = json.loads(RESUME_CACHE_FILE.read_text())
            return Resume(**cached)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Resume cache was corrupted, re-parsing.")

    resume = _parse_with_llm(resume_text)
    RESUME_CACHE_FILE.write_text(resume.model_dump_json(indent=2))
    return resume
