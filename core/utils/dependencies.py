from fastapi import Request, HTTPException, status
from core.database.database import SessionLocal
from core.schema import EnumRole


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_auth(req: Request):
    if not req.session.get("username")\
            or not req.session.get("role")\
            or not req.cookies.get("_r")\
            or req.session.get("remember") != req.cookies.get("_r"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")


def validate_privilege(req: Request):
    if req.session.get("role") != EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Feature opened to system admin only.")
