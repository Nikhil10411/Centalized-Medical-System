# ✅ token_utils.py (Refactored, Cleaned, Pydantic-v2 Ready)

from datetime import datetime, timedelta
from enum import Enum
from typing import (
    List,
)
from uuid import UUID
import os, logging

from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED
from sqlalchemy import func, cast, String 

from database import get_db
from models import User, Doctor, Patient, RoleEnum # Assuming RoleEnum is imported from models or defined below

# ───────────────────────────────
# ENV + LOG SETUP
# ───────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))
RESET_MIN = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", 10080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ───────────────────────────────
# Token Blacklist (for Logout)
# ───────────────────────────────
TOKEN_BLACKLIST = set()

def blacklist_token(token: str):
    """Add a JWT to the blacklist (e.g. on logout)."""
    TOKEN_BLACKLIST.add(token)
    logger.info(f"🛑 Token blacklisted at {datetime.utcnow()}")

def is_token_blacklisted(token: str) -> bool:
    """Check if token has been blacklisted."""
    return token in TOKEN_BLACKLIST
    
# ───────────────────────────────
# Role Enum (redeclared for clarity)
# ───────────────────────────────
class RoleEnum(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    HOSPITAL_SUPER_ADMIN = "hospital_super_admin"
    HOSPITAL_ADMIN = "hospital_admin"
    CLINIC_SUPER_ADMIN = "clinic_super_admin"
    CLINIC_ADMIN = "clinic_admin"
    PHARMACY_SUPER_ADMIN = "pharmacy_super_admin"
    PHARMACY_ADMIN = "pharmacy_admin"
    LAB = "lab"
    CHEMIST = "chemist"
    DISPENSARY_SUPER_ADMIN = "dispensary_super_admin"
    DISPENSARY_ADMIN = "dispensary_admin"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"

# ───────────────────────────────
# JWT Helpers
# ───────────────────────────────
def _exp(minutes: int) -> datetime:
    return datetime.utcnow() + timedelta(minutes=minutes)

def _encode(claims: dict) -> str:
    claims.update({"iat": datetime.utcnow(), "exp": _exp(ACCESS_MIN)})
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    if is_token_blacklisted(token):
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Token has been revoked. Please log in again.")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Invalid token")

def build_token_for_user(user: User, *, token_type: str = "access") -> str:
    return _encode({
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role,
        "is_admin": user.is_admin,
        "token_type": token_type,
    })

# ───────────────────────────────
# Reset Token Helpers
# ───────────────────────────────
def generate_reset_token(email: str) -> str:
    return jwt.encode({
        "sub": email,
        "reset": True,
        "token_type": "reset",
        "iat": datetime.utcnow(),
        "exp": _exp(RESET_MIN),
    }, SECRET_KEY, algorithm=ALGORITHM)

def decode_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("reset"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Reset token expired")
    except JWTError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Invalid reset token")

# ───────────────────────────────
# Shared Token Decoder for DI
# ───────────────────────────────
def get_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    return decode_access_token(token)

# ───────────────────────────────
# Current User Accessors
# ───────────────────────────────
def get_current_active_user(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(401, "Invalid token: user_id missing")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

def get_current_user( # The last definition of get_current_user is used
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token: user_id missing")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# ⭐ NEW FUNCTION FOR DOCTOR ROUTES ⭐
def get_current_doctor_user_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Dependency that ensures the authenticated user has the DOCTOR role 
    and returns their User ID. This ID is used as the doctor_id.
    """
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only users with the 'doctor' role can manage doctor profiles."
        )
    return str(current_user.id)
# ───────────────────────────────
# Role Guards & Validators
# ───────────────────────────────
def role_required(*roles):
    flat_roles = []

    # Support both list input and unpacked arguments
    for r in roles:
        if isinstance(r, list):
            flat_roles.extend(r)
        else:
            flat_roles.append(r)

    # Extract string values
    allowed_roles = {r.value.lower() if hasattr(r, 'value') else str(r).lower() for r in flat_roles}

    def inner(
        payload: dict = Depends(get_user_payload),
        db: Session = Depends(get_db)
    ) -> User:
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(404, "User not found")
        if user.is_admin:
            return user
        if user.role.lower() not in allowed_roles:
            raise HTTPException(403, "Access denied: role not allowed")
        return user

    return inner


def hospital_admin_required(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter_by(id=payload["user_id"]).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.role != RoleEnum.ADMIN or not user.is_admin:
        raise HTTPException(403, "Admin access denied")
    return user

def get_current_hospital_super_admin(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or user.role != RoleEnum.HOSPITAL_SUPER_ADMIN:
        raise HTTPException(403, "Not authorized")
    return user

'''def get_hospital_by_super_admin(current_user: User, db: Session) -> Hospital:
    hospital = db.query(Hospital).filter(Hospital.role_id == current_user.id).first()
    if not hospital:
        raise HTTPException(404, detail="Hospital not found for this super admin")
    return hospital
'''

def get_current_hospital_admin(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or user.role != RoleEnum.HOSPITAL_ADMIN:
        raise HTTPException(403, "Not authorized")
    return user

def get_current_hospital_admin_or_super_admin(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or user.role not in [RoleEnum.HOSPITAL_ADMIN, RoleEnum.HOSPITAL_SUPER_ADMIN]:
        raise HTTPException(403, "Not authorized")
    return user


def get_current_staff_user(user: User = Depends(get_current_active_user)) -> User:
    if user.role not in {RoleEnum.HOSPITAL_SUPER_ADMIN.value, RoleEnum.ADMIN.value}:
        raise HTTPException(403, "Access denied: Staff only")
    return user

'''def get_hospital_by_role(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Hospital:
    if user.role == RoleEnum.HOSPITAL_SUPER_ADMIN:
        return db.query(Hospital).filter(Hospital.role == user.role, Hospital.role_id == user.id).first()
    elif user.role == RoleEnum.ADMIN:
        return db.query(Hospital).filter(Hospital.role_id == user.id).first()
    raise HTTPException(403, "Unauthorized hospital access")
'''
# Assuming this is the content of your admin_required function file

def admin_required(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    """
    Enforces Admin access by strictly checking the user's 'is_admin' flag.
    This relies on the fact that only the startup user has is_admin=True.
    """
    
    # 1. Fetch the User based on the decoded token payload
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    
    if not user:
        # User not found in DB (shouldn't happen with a valid token, but safe check)
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Check the required 'is_admin' flag
    if not user.is_admin:
        # If the flag is False, block access
        raise HTTPException(
            status_code=403, 
            detail="Admin access required (User is not an administrator)"
        )
        
    # 3. Success: return the User object
    return user

def get_current_doctor(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> Doctor:
    email = payload.get("sub")
    doctor = db.query(Doctor).filter(Doctor.email == email).first()
    if not doctor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if not doctor.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Doctor account is not active")
    if not doctor.is_hospital_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Doctor is not verified by the hospital")
    return doctor

# NOTE: The second get_current_user definition is used above.

def get_current_doctor_unverified(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Doctor:
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Not authorized as doctor")

    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


def get_current_patient(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found for current user"
        )
    return patient



def get_current_admin_user(
    payload: dict = Depends(get_user_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or user.role not in [RoleEnum.HOSPITAL_SUPER_ADMIN, RoleEnum.HOSPITAL_ADMIN]:
        raise HTTPException(403, "Only hospital admins can access this resource")
    if not user.hospital_id:
        raise HTTPException(403, "Hospital ID not associated with this user")
    return user

def get_current_user_with_roles(allowed_roles: List[RoleEnum]):
    def _role_check(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return user
    return _role_check


def resolve_owner_filter(current_user):
    """
    Returns a dict to filter Product queries based on current_user role.
    """
    if current_user.role in [RoleEnum.PHARMACY_SUPER_ADMIN, RoleEnum.PHARMACY_ADMIN]:
        if not current_user.pharmacy_id:
            raise HTTPException(status_code=400, detail="User has no pharmacy assigned")
        return {"pharmacy_id": current_user.pharmacy_id}

    elif current_user.role in [RoleEnum.CHEMIST, RoleEnum.DISPENSARY_ADMIN]:
        if not current_user.store_id:
            raise HTTPException(status_code=400, detail="User has no store assigned")
        return {"store_id": current_user.store_id}

    elif current_user.role == RoleEnum.ADMIN:
        if not current_user.supplier_id:
            raise HTTPException(status_code=400, detail="User has no supplier assigned")
        return {"supplier_id": current_user.supplier_id}

    else:
        raise HTTPException(status_code=403, detail="User role not allowed to manage products")