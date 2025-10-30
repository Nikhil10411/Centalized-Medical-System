import os
from jose import JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from models import User, Doctor, Patient
from database import get_db
from .utils import decode_access_token  # your utility to decode JWTs

# ─────────────────────────────────────────────
# OAuth2 Schemes
# ─────────────────────────────────────────────
user_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
doctor_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/doctor-login")

# ─────────────────────────────────────────────
# Admin Email from ENV
# ─────────────────────────────────────────────
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")  # fallback for dev

# ─────────────────────────────────────────────
# ✅ Get Current Admin User
# ─────────────────────────────────────────────
def get_current_admin_user(token: str = Depends(user_oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email or email.lower() != ADMIN_EMAIL.lower():
            raise HTTPException(status_code=403, detail="Only admin access allowed")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─────────────────────────────────────────────
# ✅ Get Current User (Admin, SuperAdmin, Patient)
# ─────────────────────────────────────────────
def get_current_user(token: str = Depends(user_oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token missing email (sub)")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─────────────────────────────────────────────
# ✅ Get Current Patient
# ─────────────────────────────────────────────
def get_current_patient_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Patient:
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Access restricted to patients only")

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return patient


# ─────────────────────────────────────────────
# ✅ Get Current Doctor
# ─────────────────────────────────────────────
def get_current_doctor(token: str = Depends(doctor_oauth2_scheme), db: Session = Depends(get_db)) -> Doctor:
    try:
        payload = decode_access_token(token)

        if payload.get("role") != "doctor":
            raise HTTPException(status_code=403, detail="Access restricted to doctors only")

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token missing email (sub)")

        doctor = db.query(Doctor).filter(Doctor.email == email).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        return doctor

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─────────────────────────────────────────────
# ✅ Authorize Medical History (Admin only)
# ─────────────────────────────────────────────
def authorize_medical_history_access(token: str = Depends(user_oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email or email.lower() != ADMIN_EMAIL.lower():
            raise HTTPException(status_code=403, detail="Only admin can access medical history")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


