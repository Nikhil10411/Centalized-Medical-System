# app/accounts/user_router.py
from fastapi import APIRouter
from ..accounts.user_handlers import get_all_users

router = APIRouter()

@router.get("/users")
def read_users():
    return get_all_users()

