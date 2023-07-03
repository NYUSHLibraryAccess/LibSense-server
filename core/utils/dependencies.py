from fastapi import Request, HTTPException, status
from core.database.database import SessionLocal
from core.schema import EnumRole


def get_db():
    """
    Dependency to get database session.
    :return:
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_auth(req: Request):
    """
    Validate if the user is authenticated properly.
    :param req: User request object.
    :return: None
    :raise: 401_Unauthorized if failed.
    """
    if not req.session.get("username")\
            or not req.session.get("role")\
            or not req.cookies.get("_r")\
            or req.session.get("remember") != req.cookies.get("_r"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")


def validate_privilege(req: Request):
    """
    Validate if the user is System Admin
    :param req: User Request Object
    :return: None
    :raise: 401_Unauthorized if user is normal user.
    """
    if req.session.get("role") != EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Feature opened to system admin only.")
