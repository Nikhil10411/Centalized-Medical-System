from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User, Patient, Doctor
from .token_utils import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_medical_history_viewer(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)

    email = payload.get("sub")  # Corrected from 'email' to 'sub'
    role = payload.get("role")

    if not email or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if role == "admin":
        return {"role": "admin", "email": email}

    if role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.email == email).first()
        if doctor:
            return {
                "role": "doctor",
                "email": email,
                "doctor_id": doctor.doctor_id
            }
        else:
            raise HTTPException(status_code=403, detail="Doctor not found")

    if role == "patient":
        user = db.query(User).filter(User.email == email).first()
        if user:
            patient = db.query(Patient).filter(Patient.user_id == user.id).first()
            if patient:
                return {
                    "role": "patient",
                    "email": email,
                    "patient_id": str(patient.patient_id)
                }
        raise HTTPException(status_code=403, detail="Patient not found")

    raise HTTPException(status_code=403, detail="Access denied")
