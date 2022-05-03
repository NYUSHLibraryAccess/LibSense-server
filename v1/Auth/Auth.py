from fastapi import status, APIRouter, Request, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.database import crud
from core import schema

router = APIRouter(tags=["User/Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=schema.SystemUser)
def login(request: Request, db: Session = Depends(get_db), payload=Body(...)):
    user = crud.login(db, payload["username"], payload["password"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong username or password.")
    user_dict = {"username": user.username, "role": user.role}
    request.session.clear()
    request.session.update(user_dict)
    return schema.SystemUser(**user_dict)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"msg": "Successfully logged out"}


@router.post("/add_user", response_model=schema.SystemUser)
def add_user(request: Request, payload: schema.NewSystemUser, db: Session = Depends(get_db)):
    if request.session.get("role") != schema.EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized request. Please login or refresh the page")
    else:
        return crud.add_user(db, payload)

