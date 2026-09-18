# Portfolio AI Assistant

An AI-powered backend that lets recruiters ask natural-language questions
about a candidate's resume — e.g. *"What backend technologies does she know?"*
or *"Tell me about her strongest project."* — and get accurate, grounded
answers instead of having to read the whole PDF.

## How it works

1. A resume PDF is uploaded once via `/resume/upload`.
2. The text is extracted and sent to an LLM (via Groq) which converts it
   into a structured JSON object (skills, experience, education, projects)
   validated against a Pydantic schema.
3. The structured resume is **cached to disk**, so it is only parsed once —
   not on every chat message.
4. When a recruiter asks a question via `/chat`, the cached structured
   resume is injected into the system prompt, and the LLM is instructed to
   answer **only** from that data (no hallucination), as if it were the
   candidate being interviewed by HR.

## Why structured extraction instead of RAG

This project intentionally uses **structured data extraction + full-context
prompting**, not Retrieval-Augmented Generation (RAG). For a single-document,
small-context use case like one resume, embedding chunks into a vector
database adds complexity without benefit — the entire resume comfortably
fits in a single prompt. RAG becomes worthwhile when the knowledge base
is large enough that it can't fit in context (multiple documents, a full
knowledge base, etc.).

## Tech stack

- **FastAPI** — API framework
- **Groq API** — fast LLM inference (`openai/gpt-oss-120b`)
- **Pydantic** — schema validation for structured resume data
- **pypdf** — PDF text extraction

## Endpoints

| Method | Endpoint          | Description                                      |
|--------|-------------------|---------------------------------------------------|
| GET    | `/health`         | Health check for uptime monitoring                |
| POST   | `/resume/upload`  | Upload a resume PDF, parse it, and cache it        |
| GET    | `/resume/status`  | Check whether a resume has been parsed             |
| POST   | `/chat`           | Ask a question about the candidate                 |

## Running locally

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and add your GROQ_API_KEY

uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

## Example usage

```bash
curl -X POST http://localhost:8000/resume/upload \
  -F "file=@my_resume.pdf"

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What projects has she built?"}'
```

## Design decisions worth mentioning in an interview

- **Caching**: the original naive version re-parsed the PDF with the LLM
  on *every* chat request — slow and wastes API calls/cost. Parsing now
  happens once on upload and is cached to disk.
- **Error handling**: API failures, malformed PDFs, and invalid LLM output
  return clean HTTP errors instead of crashing with a raw traceback.
- **CORS**: explicitly configured allowed origins so only the deployed
  frontend (not any website) can call this API from a browser.
- **Separation of concerns**: PDF extraction, resume parsing/caching, and
  the chat logic are in separate service modules rather than one file —
  makes each piece independently testable.
