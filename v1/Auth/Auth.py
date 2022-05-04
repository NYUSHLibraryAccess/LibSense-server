from fastapi import status, APIRouter, Request, Response, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import crud
from core.utils.dependencies import get_db, validate_auth
from core import schema
from typing import List

router = APIRouter(tags=["User/Authentication"])


@router.post("/login", response_model=schema.SystemUser)
def login(request: Request, response: Response, payload: schema.LoginRequest, db: Session = Depends(get_db)):
    user = crud.login(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong username or password.")
    user_dict = {"username": user.username, "role": user.role}
    request.session.clear()
    request.session.update(user_dict)
    return schema.SystemUser(**user_dict)


@router.post("/logout", response_model=schema.BasicResponse)
def logout(request: Request):
    request.session.clear()
    return {"msg": "Successfully logged out"}


@router.get("/all_users", response_model=List[schema.SystemUser])
def all_users(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != schema.EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized request. Please login or refresh the page")
    else:
        return crud.all_users(db)


@router.post("/add_user", response_model=schema.SystemUser, dependencies=[Depends(validate_auth)])
def add_user(request: Request, payload: schema.NewSystemUser, db: Session = Depends(get_db)):
    if request.session.get("role") != schema.EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized request. Please login or refresh the page")
    else:
        return crud.add_user(db, payload)


@router.delete("/delete_user", dependencies=[Depends(validate_auth)], response_model=schema.BasicResponse)
def del_user(username: str, db: Session = Depends(get_db)):
    return crud.delete_user(db, username)


@router.get("/whoami", dependencies=[Depends(validate_auth)], response_model=schema.SystemUser)
def whoami(request: Request):
    return request.session
