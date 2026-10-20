from fastapi import FastAPI
from app.core.config import settings
from app.db.session import Base, engine
from app.models import entities  # noqa: F401
from app.api.routes import auth, documents

if len(settings.jwt_secret) < 32:
    raise RuntimeError("Set JWT_SECRET to at least 32 characters in .env")

app = FastAPI(title="AI Document Assistant API", version="0.1.0")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)  # MVP only; replace with Alembic migrations.

@app.get("/health")
def health(): return {"status": "ok"}

app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
