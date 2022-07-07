from fastapi import Request, HTTPException, status
from core.database.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_auth(req: Request):
    if not req.session.get("username") or not req.session.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")