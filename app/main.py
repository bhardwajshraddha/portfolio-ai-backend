import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.routers import chat

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Portfolio AI Assistant",
    description="Backend that lets recruiters ask questions about a candidate's resume.",
    version="1.0.0",
)

# Without this, your deployed Next.js frontend (a different origin)
# cannot call this API from the browser - the browser blocks it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/")
def home():
    return {"message": "Portfolio AI backend is running."}


@app.get("/health")
def health_check():
    """Simple endpoint for uptime monitoring / deployment health checks."""
    return {"status": "ok"}
