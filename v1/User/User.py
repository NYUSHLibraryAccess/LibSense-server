from core.models import User
from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["Users"])


@router.get("/{net_id}", response_model=User)
def get_user(net_id: int):
    return True
