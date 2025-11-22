from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
# Ensure all these utility functions (including get_current_doctor_user_id) are correctly imported
from utils.token_utils import *
from models import *
from schemas import *
import shutil
import io

router = APIRouter()


# ----------------------------------------------------------------------------------
# 1. CREATE Doctor Profile (Uses Form data + Files)
# ----------------------------------------------------------------------------------
@router.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    # Core data comes via Form fields
    name: str = Form(..., min_length=2, max_length=50),
    specialization: str = Form(..., min_length=3, max_length=50),
    age: int = Form(..., gt=24, lt=100),
    gender: GenderEnum = Form(...),
    
    medical_license_number: str = Form(..., max_length=100),
    clinic_address: str = Form(..., max_length=255),
    contact_phone: Optional[str] = Form(None, max_length=20),
    experience_years: Optional[int] = Form(0, ge=0),
    education_degree: Optional[str] = Form(None, max_length=100),
    is_available: Optional[bool] = Form(True),
    clinic_name: Optional[str] = Form(None, max_length=255),
    regulatory_body: Optional[str] = Form(None, max_length=100),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),

    # File Uploads (Mandatory License Photo)
    license_photo: UploadFile = File(..., description="Mandatory image of medical license"),
    doctor_photo: Optional[UploadFile] = File(None),
    clinic_photo: Optional[UploadFile] = File(None),

    # FIX: Use the explicit dependency that returns the ID from the JWT
    user_id: str = Depends(get_current_doctor_user_id), 
    db: Session = Depends(get_db)
):
    if db.query(Doctor).filter(Doctor.doctor_id == user_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A doctor profile already exists for this user."
        )
    
    try:
        # Read file contents
        license_photo_data = license_photo.file.read()
        doctor_photo_data = doctor_photo.file.read() if doctor_photo else None
        clinic_photo_data = clinic_photo.file.read() if clinic_photo else None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error reading file content: {e}")

    db_doctor = Doctor(
        doctor_id=user_id,
        name=name, specialization=specialization, age=age, gender=gender,
        medical_license_number=medical_license_number, contact_phone=contact_phone,
        clinic_address=clinic_address, experience_years=experience_years,
        education_degree=education_degree, is_available=is_available,
        clinic_name=clinic_name, regulatory_body=regulatory_body,
        latitude=latitude, longitude=longitude,
        license_photo=license_photo_data, doctor_photo=doctor_photo_data, clinic_photo=clinic_photo_data
    )
    
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    
    return db_doctor


# ----------------------------------------------------------------------------------
# 2. LIST Doctors
# ----------------------------------------------------------------------------------
@router.get("/get_all_doctors", response_model=List[DoctorOut])
def list_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user: User = Depends(role_required(RoleEnum.CHEMIST, RoleEnum.PATIENT, RoleEnum.DOCTOR ))):
    """List all doctor profiles with pagination."""
    return db.query(Doctor).order_by(Doctor.name).offset(skip).limit(limit).all()


# ----------------------------------------------------------------------------------
# 3. GET Single Doctor
# ----------------------------------------------------------------------------------
@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: Session = Depends(get_db),current_user: User = Depends(role_required(RoleEnum.CHEMIST, RoleEnum.PATIENT, RoleEnum.DOCTOR ))):
    """Get a single doctor profile by ID."""
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


# ----------------------------------------------------------------------------------
# 4. UPDATE Doctor Profile
# ----------------------------------------------------------------------------------
@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: str, 
    # Use Optional fields for updates
    name: Optional[str] = Form(None), specialization: Optional[str] = Form(None), 
    age: Optional[int] = Form(None), gender: Optional[GenderEnum] = Form(None),
    medical_license_number: Optional[str] = Form(None), contact_phone: Optional[str] = Form(None),
    clinic_address: Optional[str] = Form(None), experience_years: Optional[int] = Form(None),
    education_degree: Optional[str] = Form(None), is_available: Optional[bool] = Form(None),
    clinic_name: Optional[str] = Form(None), regulatory_body: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None), longitude: Optional[float] = Form(None),

    # Files are optional for PUT
    license_photo: Optional[UploadFile] = File(None, description="Optional new medical license image"),
    doctor_photo: Optional[UploadFile] = File(None),
    clinic_photo: Optional[UploadFile] = File(None),
    
    # Correct Dependency
    current_user_id: str = Depends(get_current_doctor_user_id),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    if doctor_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only update your own doctor profile."
        )

    # Collect fields that are not None and update attributes
    update_data = {
        "name": name, "specialization": specialization, "age": age, "gender": gender,
        "medical_license_number": medical_license_number, "contact_phone": contact_phone,
        "clinic_address": clinic_address, "experience_years": experience_years,
        "education_degree": education_degree, "is_available": is_available,
        "clinic_name": clinic_name, "regulatory_body": regulatory_body,
        "latitude": latitude, "longitude": longitude
    }
    
    for key, value in update_data.items():
        if value is not None:
            setattr(doctor, key, value)

    # Handle file updates
    try:
        if license_photo:
            setattr(doctor, 'license_photo', license_photo.file.read())
        if doctor_photo:
            setattr(doctor, 'doctor_photo', doctor_photo.file.read())
        if clinic_photo:
            setattr(doctor, 'clinic_photo', clinic_photo.file.read())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error reading file content: {e}")

    db.commit()
    db.refresh(doctor)
    return doctor

# ----------------------------------------------------------------------------------
# 5. DELETE Doctor Profile (FIXED for ON DELETE NO ACTION)
# ----------------------------------------------------------------------------------
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: str, 
    # ⭐ CRITICAL FIX: Changed from get_current_user_id to get_current_doctor_user_id
    current_user_id: str = Depends(get_current_doctor_user_id),
    db: Session = Depends(get_db)
):
    # 1. Authorize and Find the Doctor Profile
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        
    # Authorization: Ensure the current user is deleting their own profile
    if doctor_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only delete your own doctor profile."
        )

    # 2. Find the associated User account (Parent)
    # Since doctor_id IS the user_id, we use the same ID
    user_account = db.query(User).filter(User.id == doctor_id).first()
    
    # Safety Check (should ideally never be false if data integrity is maintained)
    if not user_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Associated user account not found."
        )

    try:
        # 3. MANUAL CASCADE DELETION: Delete the child record first.
        # This removes the Doctor profile data.
        db.delete(doctor)
        
        # 4. Delete the parent record.
        # This removes the core User account (username, password, etc.).
        db.delete(user_account)
        
        # 5. Commit the transaction
        db.commit()
    
    except Exception as e:
        db.rollback()
        # You may want better error logging here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete doctor and user account: {e}")
    
    # Successful deletion returns 204 NO CONTENT (no return body needed)
    return