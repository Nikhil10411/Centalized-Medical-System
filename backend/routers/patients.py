from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from utils.token_utils import *
from models import *
from schemas import *

router = APIRouter()

# --- Patients ---

@router.post("/patients/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient: PatientCreate, 
    current_user = Depends(get_current_user), # Dependency to get logged-in user
    db: Session = Depends(get_db)
):
    # 1. Check if the user is already a patient (optional, but recommended)
    existing_patient = db.query(Patient).filter(
        Patient.patient_id == str(current_user.id)
    ).first()
    
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Patient profile already exists for this user."
        )

    # 2. Map Pydantic data to SQLAlchemy model
    patient_data = patient.model_dump()
    
    # CRITICAL FIX: Explicitly set the patient_id to the authenticated user's ID (as a string)
    # This ensures the FK relationship to the 'users' table is satisfied.
    patient_data['patient_id'] = str(current_user.id)
    
    # Also ensure the email is consistent with the user's registered email
    if current_user.email and not patient_data.get('email'):
        patient_data['email'] = current_user.email
        
    try:
        db_patient = Patient(**patient_data)
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create patient profile: {e}"
        )

@router.get("/get_all_patients/", response_model=List[PatientOut])
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user: User = Depends(role_required( RoleEnum.DOCTOR ))):
    return db.query(Patient).order_by(Patient.created_at).offset(skip).limit(limit).all()

@router.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db), current_user: User = Depends(role_required(RoleEnum.PATIENT, RoleEnum.DOCTOR ))):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/patients/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, data: PatientUpdate, db: Session = Depends(get_db),current_user: User = Depends(role_required(RoleEnum.PATIENT, RoleEnum.DOCTOR ))):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(patient, k, v)
    db.commit()
    db.refresh(patient)
    return patient

@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, db: Session = Depends(get_db), current_user: User = Depends(role_required(RoleEnum.PATIENT, RoleEnum.DOCTOR ))):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()



