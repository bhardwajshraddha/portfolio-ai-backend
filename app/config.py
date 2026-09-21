"""
Centralized configuration.
Keeping all environment/config reads in one place makes the app
easy to reason about and easy to change later (e.g. swapping model
providers) without touching business logic.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# Where uploaded resumes are stored
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Where the parsed (structured) resume JSON is cached, so we don't
# re-parse the same PDF with the LLM on every single chat request.
CACHE_DIR = BASE_DIR / "app" / "data"
CACHE_DIR.mkdir(exist_ok=True, parents=True)
RESUME_CACHE_FILE = CACHE_DIR / "resume_cache.json"
# The resume is bundled directly in the repo so it's always available,
# even after Render's free tier wipes the filesystem on restart —
# no manual upload needed in production.
BUNDLED_RESUME_PATH = BASE_DIR / "app" / "data" / "resume.pdf"

# Allowed origins for CORS. In production this should be your actual
# deployed frontend URL, not "*".
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://your-portfolio.vercel.app",
).split(",")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to your .env file before starting the app."
    )
