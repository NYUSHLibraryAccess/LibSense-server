from core.schema import User
from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["Users"])


@router.get("/", response_model=User, description="Get basic information of user.")
def get_user(net_id: str):
    return True


@router.post("/", description="Create a new user.")
def create_user(user: User):
    return True


@router.patch("/", description="Update user information.")
def update_user(user: User):
    return True


@router.delete("/", description="Delete a user.")
def delete_user(net_id: str):
    return True
