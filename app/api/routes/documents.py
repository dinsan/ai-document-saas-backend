import json
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User, Document, Message, Analysis
from app.schemas.api import ChatRequest, EmailRequest
from app.services.extraction import ALLOWED, extract
from app.services.ai import ask, context, SYSTEM

router = APIRouter(prefix="/documents", tags=["documents"])


def owned(doc_id: str, user: User, db: Session) -> Document:
    doc = db.scalar(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    if not doc: raise HTTPException(404, "Document not found")
    return doc


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED: raise HTTPException(415, "Unsupported file type")
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "File too large")
    if not data: raise HTTPException(422, "Empty file")
    # Validate file signatures, not only client-provided MIME type.
    if file.content_type == "application/pdf" and not data.startswith(b"%PDF-"):
        raise HTTPException(415, "Invalid PDF")
    if file.content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(415, "Invalid PNG")
    if file.content_type == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
        raise HTTPException(415, "Invalid JPEG")
    if file.content_type == "image/webp" and not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
        raise HTTPException(415, "Invalid WebP")
    text = extract(data, file.content_type)
    if not text.strip(): raise HTTPException(422, "No readable text detected")
    doc = Document(user_id=user.id, filename=Path(file.filename or "document").name[:255], mime_type=file.content_type,
                   storage_path="", extracted_text=text)
    path = Path(settings.upload_dir) / user.id / doc.id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    doc.storage_path = str(path)
    db.add(doc)
    db.commit()
    return {"id": doc.id, "filename": doc.filename, "characters": len(text)}


@router.get("")
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())).all()
    return [{"id": d.id, "filename": d.filename, "created_at": d.created_at} for d in docs]


@router.get("/{doc_id}")
def detail(doc_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = owned(doc_id, user, db)
    return {"id": d.id, "filename": d.filename, "mime_type": d.mime_type, "characters": len(d.extracted_text)}


@router.post("/{doc_id}/analyze")
def analyze(doc_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = owned(doc_id, user, db)
    prompt = "Analyze the document. Return a valid JSON object with keys: summary (string), risks (array), benefits (array), important_clauses (array), questions_to_ask (array). Use only supported facts; mark uncertainties.\nDOCUMENT:\n" + d.extracted_text[
        :24000]
    raw = ask(SYSTEM + " Respond only with valid JSON.", prompt)
    try:
        result = json.loads(raw)
    except ValueError:
        raise HTTPException(502, "AI returned invalid JSON")
    db.add(Analysis(document_id=d.id, result=result))
    db.commit()
    return result


@router.post("/{doc_id}/chat")
def chat(doc_id: str, body: ChatRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = owned(doc_id, user, db)
    answer = ask(SYSTEM, f"DOCUMENT EXCERPTS:\n{context(d.extracted_text, body.question)}\n\nQUESTION: {body.question}")
    db.add_all([Message(document_id=d.id, role="user", content=body.question),
                Message(document_id=d.id, role="assistant", content=answer)])
    db.commit()
    return {"answer": answer}


@router.get("/{doc_id}/messages")
def messages(doc_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned(doc_id, user, db)
    rows = db.scalars(select(Message).where(Message.document_id == doc_id).order_by(Message.created_at)).all()
    return [{"role": m.role, "content": m.content} for m in rows]


@router.post("/{doc_id}/email-draft")
def email_draft(doc_id: str, body: EmailRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    d = owned(doc_id, user, db)
    draft = ask(SYSTEM + " Draft an email, do not claim to have sent it. Return a subject and body.",
                f"DOCUMENT EXCERPTS:\n{context(d.extracted_text, body.instruction)}\nRECIPIENT CONTEXT: {body.recipient_context}\nINSTRUCTION: {body.instruction}")
    return {"draft": draft, "sent": False}
