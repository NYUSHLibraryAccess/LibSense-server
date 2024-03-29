import time

from fastapi import status, APIRouter, Request, Response, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import crud
from core.utils.dependencies import get_db, validate_auth, validate_privilege
from core import schema
from typing import List

router = APIRouter(tags=["User/Authentication"])


@router.post("/login", response_model=schema.SystemUser)
def login(request: Request, response: Response, payload: schema.LoginRequest, db: Session = Depends(get_db)):
    user = crud.login(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong username or password.")
    user_dict = {"username": user.username, "role": user.role}
    ts = str(int(time.time()))
    user_dict["remember"] = ts
    if payload.remember:
        response.set_cookie("_r", ts, max_age=86400)
    elif payload.remember_test:
        response.set_cookie("_r", ts, max_age=30)
    else:
        response.set_cookie("_r", ts, max_age=None)
    request.session.clear()
    request.session.update(user_dict)
    return schema.SystemUser(**user_dict)


@router.post("/logout", response_model=schema.BasicResponse)
def logout(request: Request, response: Response):
    request.session.clear()
    response.delete_cookie("_r")
    return {"msg": "Successfully logged out"}


@router.get("/all-users",
            response_model=List[schema.SystemUser],
            dependencies=[Depends(validate_auth), Depends(validate_privilege)])
def all_users(request: Request, db: Session = Depends(get_db)):
    if request.session.get("role") != schema.EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized request. Please login or refresh the page.")
    else:
        return crud.all_users(db)


@router.post("/add-user",
             response_model=schema.SystemUser,
             dependencies=[Depends(validate_auth), Depends(validate_privilege)])
def add_user(request: Request, payload: schema.NewSystemUser, db: Session = Depends(get_db)):
    if request.session.get("role") != schema.EnumRole.SYS_ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized request. Please login or refresh the page.")
    else:
        return crud.add_user(db, payload)


@router.delete("/delete-user", response_model=schema.BasicResponse,
               dependencies=[Depends(validate_auth), Depends(validate_privilege)])
def del_user(username: str, db: Session = Depends(get_db)):
    return crud.delete_user(db, username)


@router.get("/whoami", dependencies=[Depends(validate_auth)], response_model=schema.SystemUser)
def whoami(request: Request):
    return request.session
