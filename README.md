# AI Document Assistant — FastAPI Backend MVP

Python/FastAPI + PostgreSQL + SQLAlchemy + JWT + PyMuPDF/Tesseract OCR + OpenAI.

## Start locally

1. Install Python 3.11+ and Docker. Install Tesseract OCR (`brew install tesseract` on macOS or `sudo apt install tesseract-ocr` on Ubuntu).
2. `cp .env.example .env`; set a **random JWT_SECRET of 32+ characters** and your `OPENAI_API_KEY`.
3. `docker compose up -d db`
4. `python -m venv .venv && source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. `uvicorn app.main:app --reload`
7. Open http://localhost:8000/docs for interactive Swagger API docs.

## API routes

- `POST /api/v1/auth/register` — email/password JSON
- `POST /api/v1/auth/login` — get bearer token
- `POST /api/v1/documents` — authenticated multipart `file` PDF/PNG/JPEG/WebP
- `GET /api/v1/documents` — own documents
- `GET /api/v1/documents/{id}` — document metadata
- `POST /api/v1/documents/{id}/analyze` — structured AI analysis
- `POST /api/v1/documents/{id}/chat` — `{ "question": "What are the risks?" }`
- `GET /api/v1/documents/{id}/messages` — conversation history
- `POST /api/v1/documents/{id}/email-draft` — `{ "instruction": "Ask for clarification about the cancellation clause", "recipient_context": "property agent" }`

## Important MVP limits before public production

- Retrieval is **lexical chunks**, not embeddings/vector RAG; it may miss relevant passages. Chat history is stored but not yet fed back into model context.
- Analysis only sends the first 24,000 characters; long documents need a map-reduce/page-based pipeline.
- The AI may hallucinate; outputs must be reviewed and are not legal advice.
- Uploads and extracted text are sensitive: add encryption at rest, deletion/retention endpoints, privacy policy, consent, access audit, backup, rate limits, background jobs, malware scanning, MIME deep validation, and safe OCR sandboxing.
- Replace `create_all` with Alembic migrations, local storage with private object storage, and synchronous OCR/AI with queued workers.
- Add AI usage metering, cost caps, retries, token limits, tests, CORS allowlist, email delivery with explicit user confirmation, and Stripe before launch.
- LLM document text is untrusted; test prompt injection and ensure no document can invoke tools.
