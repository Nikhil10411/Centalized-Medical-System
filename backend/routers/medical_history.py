from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO
import uuid

from utils.token_utils import *
from database import get_db
from models import *
from schemas import *

router = APIRouter()

# -------------------------
# Helper: UUID-safe comparison
# -------------------------
def uuid_equal(a, b):
    try:
        return str(a).lower() == str(b).lower()
    except Exception:
        return False


# -------------------------
# Helper: Convert binary to URLs
# -------------------------
def replace_binary_with_urls(history_obj):
    document_exists = history_obj.document_file is not None and len(history_obj.document_file) > 0
    image_exists = history_obj.image_file is not None and len(history_obj.image_file) > 0

    history_obj.document_file = f"/file/document/{history_obj.history_id}" if document_exists else None
    history_obj.image_file = f"/file/image/{history_obj.history_id}" if image_exists else None
    return history_obj


# ============================================================
# CREATE MEDICAL HISTORY
# ============================================================
@router.post("/create/medical_history", response_model=MedicalHistoryOut)
async def create_medical_history(
    patient_identifier: str = Form(...),
    diagnosis: Optional[str] = Form(None),
    test_results: Optional[str] = Form(None),
    medicines: Optional[str] = Form(None),
    surgery_notes: Optional[str] = Form(None),
    visit_date: Optional[datetime] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    document_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(RoleEnum.DOCTOR))
):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == str(current_user.id)).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    patient = db.query(Patient).filter(
        (Patient.email == patient_identifier) | (Patient.phone == patient_identifier)
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Read files and MIME types
    doc_data = await document_file.read() if document_file else None
    img_data = await image_file.read() if image_file else None

    history = MedicalHistory(
        history_id=str(uuid.uuid4()),
        patient_id=patient.patient_id,
        doctor_id=str(current_user.id),
        diagnosis=diagnosis,
        test_results=test_results,
        medicines=medicines,
        surgery_notes=surgery_notes,
        visit_date=visit_date or datetime.now(timezone.utc),
        document_file=doc_data,
        document_mime_type=document_file.content_type if document_file else None,
        image_file=img_data,
        image_mime_type=image_file.content_type if image_file else None,
        latitude=latitude,
        longitude=longitude,
    )

    db.add(history)
    db.commit()
    db.refresh(history)
    return replace_binary_with_urls(history)


# ============================================================
# GET ALL MEDICAL HISTORIES
# ============================================================
@router.get("/get_all/medical_history", response_model=List[MedicalHistoryOut])
def get_all_medical_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(MedicalHistory).options(
        joinedload(MedicalHistory.patient),
        joinedload(MedicalHistory.doctor)
    )

    if current_user.role == RoleEnum.DOCTOR:
        histories = query.filter(MedicalHistory.doctor_id == str(current_user.id)).all()
    elif current_user.role == RoleEnum.PATIENT:
        histories = query.filter(MedicalHistory.patient_id == str(current_user.id)).all()
    elif current_user.role in [RoleEnum.HOSPITAL_ADMIN, RoleEnum.HOSPITAL_SUPER_ADMIN]:
        histories = query.all()
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    return [replace_binary_with_urls(h) for h in histories]


# ============================================================
# GET SINGLE MEDICAL HISTORY
# ============================================================
@router.get("/get_single_history/{history_id}", response_model=MedicalHistoryOut)
def get_medical_history(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = (
        db.query(MedicalHistory)
        .options(joinedload(MedicalHistory.patient), joinedload(MedicalHistory.doctor))
        .filter(MedicalHistory.history_id == history_id)
        .first()
    )

    if not history:
        raise HTTPException(status_code=404, detail="Medical history not found")
    
    if not (uuid_equal(current_user.id, history.doctor_id) or uuid_equal(current_user.id, history.patient_id)):
        raise HTTPException(status_code=403, detail="Access denied")

    return replace_binary_with_urls(history)


# ============================================================
# UPDATE MEDICAL HISTORY
# ============================================================
@router.put("/update/{history_id}", response_model=MedicalHistoryOut)
async def update_medical_history(
    history_id: str,
    diagnosis: Optional[str] = Form(None),
    test_results: Optional[str] = Form(None),
    medicines: Optional[str] = Form(None),
    surgery_notes: Optional[str] = Form(None),
    visit_date: Optional[datetime] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    document_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(RoleEnum.DOCTOR))
):
    history = db.query(MedicalHistory).filter(MedicalHistory.history_id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    if not uuid_equal(current_user.id, history.doctor_id):
        raise HTTPException(status_code=403, detail="Only the doctor who created this record can update it.")

    # Update text fields
    for field, value in {
        "diagnosis": diagnosis,
        "test_results": test_results,
        "medicines": medicines,
        "surgery_notes": surgery_notes,
        "visit_date": visit_date,
        "latitude": latitude,
        "longitude": longitude,
    }.items():
        if value is not None:
            setattr(history, field, value)

    # Update files
    if document_file:
        history.document_file = await document_file.read()
        history.document_mime_type = document_file.content_type
    if image_file:
        history.image_file = await image_file.read()
        history.image_mime_type = image_file.content_type

    db.commit()
    db.refresh(history)
    return replace_binary_with_urls(history)


# ============================================================
# DELETE MEDICAL HISTORY
# ============================================================
@router.delete("/delete/{history_id}")
def delete_medical_history(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(MedicalHistory).filter(MedicalHistory.history_id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    if not (uuid_equal(current_user.id, history.doctor_id) or current_user.role in [RoleEnum.HOSPITAL_ADMIN, RoleEnum.HOSPITAL_SUPER_ADMIN]):
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(history)
    db.commit()
    return {"message": "Medical history deleted successfully"}


# =========================================================
# DOCUMENT FILE ROUTE — View or Download (Header Auth)
# =========================================================
@router.get("/file/document/{history_id}")
def get_document_file(
    history_id: str,
    download: Optional[bool] = Query(False, description="Set to true to download instead of view"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve PDF or other document securely (view/download)."""
    history = db.query(MedicalHistory).filter(MedicalHistory.history_id == history_id).first()
    if not history or not history.document_file:
        raise HTTPException(status_code=404, detail="Document not found")

    # ✅ Allow access for patient, doctor, or admin roles
    if not (
        uuid_equal(current_user.id, history.patient_id)
        or uuid_equal(current_user.id, history.doctor_id)
        or current_user.role in [RoleEnum.HOSPITAL_ADMIN, RoleEnum.HOSPITAL_SUPER_ADMIN]
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    mime_type = history.document_mime_type or "application/pdf"
    filename = f"document_{history_id}.pdf"

    headers = {
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{filename}"'
    }

    return StreamingResponse(BytesIO(history.document_file), media_type=mime_type, headers=headers)


# =========================================================
# IMAGE FILE ROUTE — View or Download (Header Auth)
# =========================================================
@router.get("/file/image/{history_id}")
def get_image_file(
    history_id: str,
    download: Optional[bool] = Query(False, description="Set to true to download instead of view"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve image securely (view/download)."""
    history = db.query(MedicalHistory).filter(MedicalHistory.history_id == history_id).first()
    if not history or not history.image_file:
        raise HTTPException(status_code=404, detail="Image not found")

    if not (
        uuid_equal(current_user.id, history.patient_id)
        or uuid_equal(current_user.id, history.doctor_id)
        or current_user.role in [RoleEnum.HOSPITAL_ADMIN, RoleEnum.HOSPITAL_SUPER_ADMIN]
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    mime_type = history.image_mime_type or "image/jpeg"
    filename = f"image_{history_id}.jpg"

    headers = {
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{filename}"'
    }

    return StreamingResponse(BytesIO(history.image_file), media_type=mime_type, headers=headers)
