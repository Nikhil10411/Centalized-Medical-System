# backend/routers/auth.py
from __future__ import annotations

import re, logging
from datetime import datetime
from uuid import UUID
from typing_extensions import (
    List as TypingList,
)

from fastapi import (
    APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
)
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError
from pydantic import EmailStr
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models import User, Doctor
from schemas import (
    UserCreate, UserResponse, Token, ForgotPasswordRequest,
    ResetPasswordRequest
)
from utils.utils import hash_password, verify_password
from utils.token_utils import (
    build_token_for_user, decode_access_token, generate_reset_token,
    decode_reset_token, admin_required, RoleEnum, blacklist_token, 
    TOKEN_BLACKLIST, get_current_user
)
from utils.email_utils import send_reset_email
from utils.dependencies import get_current_admin_user

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth = OAuth2PasswordBearer(tokenUrl="auth/login")

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  Password policy helper
# ──────────────────────────────────────────────────────────────
def validate_pw(pwd_: str):
    if (
        len(pwd_) < 8
        or not re.search(r"[A-Z]", pwd_)
        or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd_)
    ):
        raise HTTPException(
            400,
            "Password must be at least 8 characters long, with one uppercase and one special character."
        )

# ──────────────────────────────────────────────────────────────
# 1. Signup Route (only limited roles allowed directly)
# ──────────────────────────────────────────────────────────────
@router.post("/signup", response_model=Token, tags=["Auth"])
def signup(body: UserCreate, db: Session = Depends(get_db)):
    try:
        # Prevent reserved roles from signing up directly
        reserved_roles = [
            RoleEnum.HOSPITAL_ADMIN,
            RoleEnum.ADMIN,
            "hospital_staff"
        ]
        if body.role.lower() in reserved_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You cannot sign up as this role. Please contact your hospital administrator."
            )

        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")

        validate_pw(body.password)

        user = User(
            username=body.username,
            email=body.email,
            role=body.role,
            hashed_password=hash_password(body.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log.info(f"✅ New user signed up: {user.email} as {user.role}")

        return {
            "access_token": build_token_for_user(user),
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        log.error(f"❌ Database error during signup: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup failed. Try again later.")

    except Exception as e:
        log.exception("Unexpected error during signup")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# ──────────────────────────────────────────────────────────────
# 2. Login
# ──────────────────────────────────────────────────────────────
@router.post("/login", response_model=Token, tags=["Auth"])
def user_login(creds: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(
            (User.username == creds.username) | (User.email == creds.username)
        ).first()

        if not user or not verify_password(creds.password, user.hashed_password):
            raise HTTPException(401, "Invalid credentials")

        return {
            "access_token": build_token_for_user(user),
            "token_type": "bearer",
        }
    except Exception as e:
        log.exception("Login failed")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


# ──────────────────────────────────────────────────────────────
# 4. Forgot / Reset Password
# ──────────────────────────────────────────────────────────────
@router.post("/forgot-password", tags=["Auth"])
async def forgot_password(req: ForgotPasswordRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(404, "User not found")

    token = generate_reset_token(user.email)
    reset_link = f"https://your-app.com/reset?token={token}"
    background.add_task(send_reset_email, user.email, reset_link)
    log.info("Sent reset link to %s", user.email)
    return {"msg": "Password-reset link emailed"}

@router.post("/reset-password", tags=["Auth"])
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = decode_reset_token(body.token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    validate_pw(body.new_password)
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"msg": "Password updated"}

@router.post("/logout", tags=["Auth"])
def logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Invalidate the user's access token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid authorization header")

    token = auth_header.split(" ")[1]
    blacklist_token(token)
    log.info(f"🔒 User logged out: {current_user.email}")
    return {"msg": "Successfully logged out"}


# ──────────────────────────────────────────────────────────────
# 5. Me / Token Debug
# ──────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse, tags=["Auth"])
def me(token: str = Depends(oauth), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Invalid token")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(404, "User not found")

        return user
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

@router.get("/debug/token", tags=["Debug"])
def debug_token(token: str = Depends(oauth)):
    try:
        return decode_access_token(token)
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


# ──────────────────────────────────────────────────────────────
# 6. Admin-only: TypingList & Delete Users
# ──────────────────────────────────────────────────────────────
@router.get("/users", response_model=TypingList[UserResponse],
            dependencies=[Depends(admin_required)], tags=["Admin"])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.delete("/users/{user_id}", status_code=204,
               dependencies=[Depends(admin_required)], tags=["Admin"])
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_admin:
        raise HTTPException(403, "Cannot delete an admin user")

    db.delete(user)
    db.commit()
