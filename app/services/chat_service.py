import logging

from fastapi import HTTPException
from groq import APIError, APIStatusError

from app.models.resume import Resume
from app.services.llm_client import client, MODEL_NAME

logger = logging.getLogger(__name__)


def ask_candidate(question: str, resume: Resume) -> str:
    """
    Answers a recruiter's question strictly using the candidate's
    resume data. The system prompt explicitly forbids hallucination.
    """
    system_prompt = f"""
You are an AI assistant representing a job candidate.

Below is everything you know about the candidate:

{resume.model_dump_json(indent=2)}

Rules:
1. Answer only using this information.
2. Never hallucinate or invent details not present above.
3. If information is unavailable, say "I don't have enough information to answer that."
4. Be professional and concise.
5. Answer as if HR is interviewing this candidate.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
    except (APIError, APIStatusError) as e:
        logger.error("Groq API error while answering question: %s", e)
        raise HTTPException(status_code=502, detail="AI assistant is temporarily unavailable. Please try again shortly.")

    return response.choices[0].message.content
