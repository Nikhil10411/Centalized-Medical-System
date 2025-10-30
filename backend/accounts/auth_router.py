# app/accounts/auth_router.py
from fastapi import APIRouter, HTTPException
from models import UserSignup, UserLogin
from ..accounts.auth_handlers import signup_user, login_user

router = APIRouter()

@router.post("/signup")
def signup(user: UserSignup):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    signup_user(user)
    return {"msg": "User created successfully"}

@router.post("/login")
def login(user: UserLogin):
    token = login_user(user)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}
