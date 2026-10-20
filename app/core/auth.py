from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User

passwords = PasswordHash.recommended()
bearer = HTTPBearer()

def token_for(user_id: str):
    return jwt.encode({"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=12)}, settings.jwt_secret, algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, payload["sub"])
        if user: return user
    except (jwt.PyJWTError, KeyError):
        pass
    raise HTTPException(401, "Invalid or expired token")
