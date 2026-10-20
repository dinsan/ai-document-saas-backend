from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User
from app.schemas.api import Register, Login
from app.core.auth import passwords, token_for

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(body: Register, db: Session = Depends(get_db)):
    email = str(body.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(email=email, password_hash=passwords.hash(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}

@router.post("/login")
def login(body: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if not user or not passwords.verify(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": token_for(user.id), "token_type": "bearer"}
