from decimal import Decimal
import base64
import re
import uuid
from uuid import UUID
from datetime import date, datetime, time
from enum import Enum
from typing import (
    Annotated,
    Literal,
    Union,
    Optional,
    List,
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationInfo,
    constr,
    model_validator,
    field_validator,
    ConfigDict,
    condecimal,
    Base64Str,
    UUID4
)

# ───────────────────────────────────────
# Base helpers
# ───────────────────────────────────────
class BaseSchema(BaseModel):
    model_config = {
        "from_attributes": True,   # replaces orm_mode=True in Pydantic v2
        "populate_by_name": True,  # allows alias mapping if needed
    }

class ConfigOrm:
    model_config = ConfigDict(from_attributes=True)

# ------------------------
# Universal For all project
# ------------------------
class UniversalOTPLoginRequest(BaseModel):
    identifier: Union[EmailStr, constr(min_length=10, max_length=12)]
    method: Literal["email", "phone", "aadhaar"]

class UniversalOTPVerifyRequest(BaseModel):
    identifier: Union[EmailStr, constr(min_length=10, max_length=12)]
    method: Literal["email", "phone", "aadhaar"]
    otp: constr(min_length=6, max_length=6, pattern=r"^\d{6}$")

# ------------------------
# User Models
# ------------------------
class Role(str, Enum):
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

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: constr(min_length=8, max_length=50)
    confirm_password: str
    role: Role = Role.PATIENT

    @field_validator("confirm_password")
    def passwords_match(cls, v: str, info: ValidationInfo):
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Passwords do not match")
        return v

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: Role
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    msg: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, v: str, info: ValidationInfo):
        new_password = info.data.get("new_password")
        if new_password and v != new_password:
            raise ValueError("Passwords do not match")
        return v

class MessageResponse(BaseModel):
    msg: str

class TokenPayloadResponse(BaseModel):
    sub: EmailStr
    role: str
    exp: int

# -------------------------
# Doctor Schemas
# -------------------------

class GenderEnum(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"

# ----------------------------------------------------------------------
# 1. DoctorBase: Defines fields common to Create, Update, and Response
# ----------------------------------------------------------------------
class DoctorBase(BaseModel):
    # Core Fields (Retained)
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=24, lt=100, description="Age must be between 25 and 99")
    gender: GenderEnum
    specialization: str = Field(..., min_length=3, max_length=50)
    
    # ✅ LOGICAL PROFESSIONAL FIELDS
    medical_license_number: str = Field(..., max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    experience_years: Optional[int] = Field(0, ge=0, description="Years of experience cannot be negative")
    education_degree: Optional[str] = Field(None, max_length=100)
    is_available: Optional[bool] = True
    
    # ✅ CLINIC & REGULATORY FIELDS
    clinic_name: Optional[str] = Field(None, max_length=255)
    clinic_address: str = Field(..., max_length=255) # Mandatory address
    regulatory_body: Optional[str] = Field(None, max_length=100)

    # ✅ LOCATION FIELDS
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Note: Binary/File fields (doctor_photo, license_photo, clinic_photo) 
    # are often handled outside Pydantic in FastAPI using File Uploads or URLs.
    # We omit the LargeBinary fields from the Pydantic model for simplicity
    # and typically use separate endpoints for file uploads.


# ----------------------------------------------------------------------
# 2. DoctorCreate: Used for receiving data to create a new profile
# ----------------------------------------------------------------------
class DoctorCreate(DoctorBase):
    pass
    

# ----------------------------------------------------------------------
# 3. DoctorUpdate: Used for receiving data to modify an existing profile
# ----------------------------------------------------------------------
class DoctorUpdate(DoctorBase):
    # Make all fields optional for partial updates, except perhaps the license number
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[GenderEnum] = None
    specialization: Optional[str] = None
    
    # medical_license_number is often excluded from updates or kept as is
    clinic_address: Optional[str] = None # Allow updating address
    
    
# ----------------------------------------------------------------------
# 4. DoctorOut (Final API Response Model) - FIX APPLIED HERE
# ----------------------------------------------------------------------
class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    doctor_id: str
    
    # Core Fields
    name: str
    age: int
    gender: GenderEnum
    specialization: str
    
    # Professional & Contact
    medical_license_number: str
    contact_phone: Optional[str]

    # ⭐ FIX 1 & 2: Mark fields that were previously failing with 'Input should be a valid...'
    # as Optional, allowing None (NULL from DB) to be passed.
    experience_years: Optional[int] # <-- CHANGED from 'experience_years: int'
    education_degree: Optional[str]
    is_available: Optional[bool]     # <-- CHANGED from 'is_available: bool'

    # Clinic & Location
    clinic_name: Optional[str]
    clinic_address: str
    regulatory_body: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    
    # ⭐ FIX 3 & 4: Mark Timestamps as Optional, as they returned None for existing rows.
    created_at: Optional[datetime]  # <-- CHANGED from 'created_at: datetime'
    updated_at: Optional[datetime]  # <-- CHANGED from 'updated_at: datetime'
    
    # --- RETAINED CUSTOM VALIDATORS ---

    @field_validator("age")
    @classmethod
    def age_must_be_above_24(cls, v: int) -> int:
        if v <= 24:
            raise ValueError("Doctor age must be greater than 24")
        return v

    @field_validator("gender")
    @classmethod
    def gender_must_be_valid(cls, v: GenderEnum) -> GenderEnum:
        # Pydantic handles Enum validation, but keeping this for robustness
        allowed = {"Male", "Female", "Other"}
        if v.value not in allowed:
            raise ValueError("Input should be 'Male', 'Female' or 'Other'")
        return v
                
class DoctorOTPLoginInput(BaseModel):
    email: EmailStr


class DoctorOTPVerifyInput(BaseModel):
    email: EmailStr
    otp: constr(min_length=6, max_length=6, pattern=r"^\d{6}$")


class DoctorAadhaarOTPLoginInput(BaseModel):
    aadhaar_number: constr(min_length=12, max_length=12, pattern=r"^\d{12}$")


class DoctorAadhaarOTPVerifyInput(BaseModel):
    aadhaar_number: constr(min_length=12, max_length=12, pattern=r"^\d{12}$")
    otp: constr(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PhoneRequest(BaseModel):
    phone_number: str


class DoctorPublicResponse(BaseModel):
    doctor_id: UUID
    hospital_id: UUID
    name: str
    age: int
    gender: str
    aadhaar_number: str
    specialization: str
    experience_year: int
    phone_number: str
    email: EmailStr
    created_at: datetime
    photo_url: Optional[str] = None
    license_file_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ------------------------
# Patient Schemas
# ------------------------

class PatientBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[constr(min_length=10, max_length=10, pattern=r"^[6789]\d{9}$")] = None
    
    age: Optional[int] = Field(None, ge=0, le=150, description="Age must be between 0 and 150")
    gender: Optional[Literal["male", "female", "other", "Male", "Female", "Other"]] = None
    
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    pin_code: Optional[str] = Field(None, max_length=20)
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PatientCreate(PatientBase):
    """Schema for creating new patients"""
    pass


class PatientUpdate(PatientBase):
    """Schema for updating patient details"""
    pass


class PatientResponse(PatientBase):
    patient_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
class PatientOut(BaseModel):
    patient_id: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    pin_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



# ------------------------
# Medical History Models
# ------------------------

# ------------------------
# Patient Slim Model
# ------------------------
class PatientSlim(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True
# ------------------------
# Doctor Slim Model
# ------------------------
class DoctorSlim(BaseModel):
    name: str
    contact_phone: Optional[str] = None
    specialization: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    class Config:
        from_attributes = True

class MedicalHistoryBase(BaseModel):
    diagnosis: Optional[str] = None
    test_results: Optional[str] = None
    medicines: Optional[str] = None
    surgery_notes: Optional[str] = None
    visit_date: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MedicalHistoryCreate(MedicalHistoryBase):
    # ⚠️ Removed patient_id to prevent tampering by doctor
    # The backend will auto-fetch based on authorized doctor-patient logic
    document_file: Optional[bytes] = None
    image_file: Optional[bytes] = None


class MedicalHistoryOut(MedicalHistoryBase):
    history_id: str
    doctor_id: str
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientSlim] = None  # ✅ nested patient info
    doctor: Optional[DoctorSlim] = None    # ✅ nested doctor info
    
    document_file: Optional[str] = None
    image_file: Optional[str] = None
    
    class Config:
        from_attributes = True


####################################

class HospitalBase(BaseModel):
    name: str
    address: str
    phone: constr(min_length=10, max_length=15, pattern=r"^[6789]\d{9}$")
    email: EmailStr
    established_year: str
    type: str
    is_paperLess: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    established_year: Optional[str] = None
    type: Optional[str] = None
    is_paperLess: Optional[bool] = None
    updated_at: Optional[datetime] = None


class HospitalOut(HospitalBase, ConfigOrm):
    hospital_id: UUID


# ───────────────────────────────────────
# 2. Department
# ───────────────────────────────────────
class DepartmentBase(BaseModel):
    name: Optional[str] = None
    floor: Optional[Union[int, str]] = None

    @field_validator("floor", mode="before")
    @classmethod
    def normalize_floor(cls, v):
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            return v.strip().lower()
        return v


# Create schema
class DepartmentCreate(DepartmentBase):
    pass


# Update schema
class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    floor: Optional[Union[int, str]] = None


# Output schema
class DepartmentOut(DepartmentBase, ConfigOrm):
    department_id: UUID
    hospital_id: UUID

# ───────────────────────────────────────
# 3. Room
# ───────────────────────────────────────
class RoomBase(BaseModel):
    room_no: str = Field(..., max_length=10)
    bed_count: int = Field(1, ge=1)
    type: Optional[str] = Field(default=None, max_length=50)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_no: Optional[str] = None
    bed_count: Optional[int] = None
    type: Optional[str] = None


class RoomOut(RoomBase, ConfigOrm):
    room_id: UUID
    department_id: UUID

# ───────────────────────────────────────
# 5. Hospital Services
# ───────────────────────────────────────

class ServiceBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    price: Optional[Decimal] = None
    is_available: Optional[bool] = True
    availability_schedule: Optional[str] = Field(
        default=None,
        description="Optional field like 'Mon-Fri: 9AM–5PM'"
    )


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    is_available: Optional[bool] = None
    availability_schedule: Optional[str] = None


class ServiceOut(ServiceBase, ConfigOrm):
    service_id: UUID
    price: float  # Ensure float for external response (Decimal → float)
    is_available: bool

# ───────────────────────────────────────────
# 5. Doctor Duty Schemas
# ───────────────────────────────────────────
class DutyBase(BaseModel):
    week_start: str                      # e.g. "Monday"
    week_end: str                        # e.g. "Sunday"
    weekday: str                         # e.g. "Wednesday"
    start_time: str                      # e.g. "09:00 AM"
    end_time: str                        # e.g. "05:00 PM"
    lunch_break: Optional[str] = None    # e.g. "1:00 PM - 2:00 PM"
    is_on_duty: Optional[bool] = True

    department_name: Optional[str] = None
    doctor_name: Optional[str] = None
    shift: Optional[str] = None

    @field_validator("start_time", "end_time", "lunch_break", mode="before")
    @classmethod
    def parse_time_str(cls, v: str) -> str:
        if isinstance(v, time):
            return v.strftime("%I:%M %p").lstrip("0")  # Format to 12-hour clock
        if isinstance(v, str):
            v = v.strip().upper()
            try:
                # Match AM/PM format
                if re.match(r"^\d{1,2}:\d{2}\s?(AM|PM)$", v):
                    datetime.strptime(v, "%I:%M %p")
                    return v
                # Match 24-hour format
                elif re.match(r"^\d{1,2}:\d{2}$", v):
                    t = datetime.strptime(v, "%H:%M")
                    return t.strftime("%I:%M %p").lstrip("0")
                # Match range (lunch break)
                elif "-" in v and ("AM" in v or "PM" in v):
                    parts = v.split("-")
                    if len(parts) == 2:
                        datetime.strptime(parts[0].strip(), "%I:%M %p")
                        datetime.strptime(parts[1].strip(), "%I:%M %p")
                        return f"{parts[0].strip()} - {parts[1].strip()}"
            except Exception:
                pass
        raise ValueError("Time must be 'HH:MM AM/PM', 'HH:MM' (24h), or 'HH:MM AM/PM - HH:MM PM' for lunch")

    @model_validator(mode="after")
    def check_start_and_end(self):
        fmt = "%I:%M %p"
        try:
            start = datetime.strptime(self.start_time, fmt)
            end = datetime.strptime(self.end_time, fmt)
            if end <= start:
                raise ValueError("End time must be after start time")
        except Exception:
            raise ValueError("Invalid time format")
        return self


class DutyCreate(DutyBase):
    doctor_id: UUID


class DutyUpdate(BaseModel):
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    weekday: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    lunch_break: Optional[str] = None
    is_on_duty: Optional[bool] = None
    department_name: Optional[str] = None
    doctor_name: Optional[str] = None
    shift: Optional[str] = None


class DutyOut(DutyBase, ConfigOrm):
    duty_id: UUID
    doctor_id: UUID

# ───────────────────────────────────────
# 6. Appointment (if you expose via API)
# ───────────────────────────────────────
class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    appointment_date: date
    appointment_time: time

class AppointmentOut(AppointmentBase, ConfigOrm):
    appointment_id: UUID
    hospital_id: UUID
    status: str

#########################################################

class HospitalStaffBase(BaseModel):
    full_name: str
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., pattern="^(male|female|other)$")
    role: str
    designation: Optional[str] = None
    department_name: Optional[str] = None
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    phone_number: str
    email: Optional[EmailStr] = None
    mci_state: Optional[str] = None
    mci_number: Optional[str] = None
    salary: Optional[float] = None
    joined_date: date
    employment_type: Optional[str] = "full_time"
    shift: Optional[str] = "day"

class HospitalStaffCreate(HospitalStaffBase):
    staff_photo: Optional[bytes] = None
    aadhaar_photo: Optional[bytes] = None
    certificate_uploaded: Optional[bytes] = None

class HospitalStaffOut(HospitalStaffBase):
    staff_id: UUID
    hospital_id: UUID
    user_id: UUID
    department_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HospitalStaffUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    department_name: Optional[str] = None
    aadhaar_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    mci_state: Optional[str] = None
    mci_number: Optional[str] = None
    salary: Optional[float] = None
    joined_date: Optional[date] = None
    employment_type: Optional[str] = None
    shift: Optional[str] = None
    staff_photo: Optional[bytes] = None
    aadhaar_photo: Optional[bytes] = None
    certificate_uploaded: Optional[bytes] = None

# ───────────────────────────────────────────
# 5. Doctor verfication Schemas
# ───────────────────────────────────────────


class VerificationTypeEnum(str, Enum):
    digital = "digital"
    in_person = "in_person"

class VerificationStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class DoctorVerificationSlotOut(BaseModel):
    slot_id: UUID 
    start_time: datetime
    end_time: datetime
    is_booked: bool
    hospital_id: UUID
    hospital_name: str
    hospital_type: str
    hospital_address: str

    model_config = ConfigDict(from_attributes=True)

class DoctorVerificationSlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

class DoctorVerificationBookSlot(BaseModel):
    hospital_name: str
    start_time: datetime
    doctor_name: str
    mci_number: str
    verification_type: VerificationTypeEnum

class DoctorVerificationOut(BaseModel):
    doctor_name: str
    verification_status: VerificationStatusEnum
    verification_type: VerificationTypeEnum

    model_config = ConfigDict(from_attributes=True)

class VerificationStatusUpdate(BaseModel):
    doctor_name: str
    verification_status: VerificationStatusEnum
    verification_type: VerificationTypeEnum
    comment: Optional[str] = None

class SlotBookingRequest(BaseModel):
    hospital_name: str
    start_time: datetime
    verification_type: VerificationTypeEnum

class SlotBookingResponse(BaseModel):
    message: str
    scheduled_at: datetime
    hospital_name: str

class SlotBookingByIdRequest(BaseModel):
    slot_id: str
    verification_type: VerificationTypeEnum



# -------------------------
# Medical Store
# -------------------------
class MedicalStoreBase(BaseModel):
    store_name: str
    owner_name: str
    age: Optional[int] = Field(None, ge=18, le=120, description="Owner's age (18-120)")
    gender: Optional[str] = None   

    store_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = Field(
        default=None,
        description="Indian phone number must be 10 digits starting with 6/7/8/9"
    )
    email: Optional[str] = Field(
        default=None,
        description="Valid email address"
    )

    open_hours: Optional[str] = None
    delivery_radius_km: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # ✅ Phone validation for Indian numbers
    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) != 10 or not v.isdigit() or v[0] not in "6789":
            raise ValueError("Phone must be a valid 10-digit Indian number starting with 6/7/8/9")
        return v

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v in ["male", "female", "other"]:
            return v.capitalize()   # → "Male", "Female", "Other"
        raise ValueError("Gender must be Male, Female, or Other")

   

# -------------------------
# Create schema (input)
# -------------------------
class MedicalStoreCreate(MedicalStoreBase):
    license_document: bytes
    license_mime: Optional[str] = None
    store_photo: bytes
    photo_mime: Optional[str] = None

    

# -------------------------
# Update schema (partial)
# -------------------------
class MedicalStoreUpdate(BaseModel):
    store_name: Optional[str] = None
    owner_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    gender: Optional[str] = None   

    store_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    open_hours: Optional[str] = None
    delivery_radius_km: Optional[int] = None
    license_document: Optional[bytes] = None
    license_mime: Optional[str] = None
    store_photo: Optional[bytes] = None
    photo_mime: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # ✅ Reuse validator for Indian phone
    @field_validator("phone")
    @classmethod
    def validate_indian_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) != 10 or not v.isdigit() or v[0] not in "6789":
            raise ValueError("Phone must be a valid 10-digit Indian number starting with 6/7/8/9")
        return v

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v in ["male", "female", "other"]:
            return v.capitalize()   # → "Male", "Female", "Other"
        raise ValueError("Gender must be Male, Female, or Other")

# -------------------------
# Response schema (output)
# -------------------------
class MedicalStoreResponse(MedicalStoreBase):
    store_id: UUID
    owner_id: UUID
    created_at: datetime
    store_photo: Optional[str] = None   # Base64 encoded or URL
    photo_mime: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
class MedicalStoreCreateSuccess(BaseModel):
    message: str
    store: MedicalStoreResponse

    model_config = ConfigDict(from_attributes=True)

# -------------------------
# Base schema
# -------------------------
class SupplierBase(BaseModel):
    supplier_name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pin_code: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["Male", "Female", "Other", "male", "female", "other"]] = None

# -------------------------
# Create schema
# -------------------------
class SupplierCreate(SupplierBase):
    # Add created_by to set who created the supplier (user ID string)
    created_by: Optional[str] = None

# -------------------------
# Update schema
# -------------------------
class SupplierUpdate(SupplierBase):
    # Allow updating created_by if needed (optional)
    #created_by: Optional[str] = None
    pass

# -------------------------
# Response schema
# -------------------------
class SupplierResponse(SupplierBase):
    supplier_id: str
    created_at: datetime
    created_by: Optional[str] = None  # Include in response for info if needed

    model_config = ConfigDict(from_attributes=True)

# -------------------------
# Product (Medicine)
# -------------------------
class ProductBase(BaseModel):
    name: str
    brand: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None
      # ✅ required for linking product to a store


class ProductCreate(ProductBase):
    """
    For product creation via API.
    Image is uploaded separately as UploadFile in the route,
    not part of the JSON body.
    """
    pass
class ProductUpdate(ProductBase):
    name: Optional[str] = None
    brand: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    category: Optional[str] = None
    hsn_code: Optional[str] = None


class ProductResponse(ProductBase):
    product_id: str
    image_mime: Optional[str] = None  # ✅ return type of uploaded image
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------
# Inventory
# -------------------------
class ProductNested(BaseModel):
    brand: Optional[str]
    generic_name: Optional[str]
    dosage: Optional[str]
    form: Optional[str]
    category: Optional[str]

    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    product_name: str
    batch_no: str
    expiry_date: datetime
    quantity: int
    price: condecimal(max_digits=18, decimal_places=2) 

class InventoryCreate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    inventory_id: UUID
    store_id: UUID
    product_id: UUID
    created_at: datetime
    last_updated: datetime
    product: ProductNested  # Nested Product schema

    class Config:
        from_attributes = True


# -------------------------
# Customer Schemas
# -------------------------

class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    role: Optional[str] = Field(default="CUSTOMER")   # Default role
    age: Optional[int] = None
    gender: Optional[Literal["Male", "Female", "Other", "male", "female", "other"]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    pass


class CustomerUpdate(CustomerBase):
    """Schema for updating a customer"""
    pass


class CustomerResponse(CustomerBase):
    customer_id: str
    store_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# -------------------------
# Prescription Schemas
# -------------------------
class PatientNested(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 

class customerNested(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["Male", "Female", "Other", "male", "female", "other"]] = None

    model_config = ConfigDict(from_attributes=True)  


class PrescriptionCreate(BaseModel):
    doctor_name: Optional[str] = None
    notes: Optional[str] = None

class PrescriptionResp(BaseModel):
    prescription_id: str
    customer_id: Optional[str] = None
    patient_id: Optional[str] = None
    store_id: Optional[str] = None
    doctor_name: Optional[str]
    notes: Optional[str]
    file_mime: Optional[str]
    created_at: datetime
    patient: Optional[PatientNested] = None # Expects a loaded Patient object
    customer: Optional[customerNested] = None # Expects a loaded Patient object

    model_config = ConfigDict(from_attributes=True)  

# ------------------------------
# Prescription Response Schemas
# ------------------------------
class MedicalStoreResponse(BaseModel):
    store_name: Optional[str] = None
    owner_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=120)
    gender: Optional[str] = None   

    store_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    open_hours: Optional[str] = None
    delivery_radius_km: Optional[int] = None
    store_photo: Optional[str] = Field(None, alias='store_photo_b64') # <--- Read the encoded property
    photo_mime: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PrescriptionResponseBase(BaseModel):
    prescription_id: str
    status: Optional[str] = Field(None, description="CONFIRMED / PARTIAL / NOT AVAILABLE")
    available_items_json: Optional[str] = None
    message: Optional[str] = None

class PrescriptionResponseCreate(PrescriptionResponseBase):
    pass  # store_id removed — backend determines this

class PrescriptionResponseUpdate(BaseModel):
    status: Optional[str] = None
    available_items_json: Optional[str] = None
    message: Optional[str] = None

class PrescriptionResponseRead(BaseModel):
    response_id: str
    prescription_id: str
    store_id: Optional[str]
    status: Optional[str]
    available_items_json: Optional[str]
    message: Optional[str]
    responded_at: datetime
    MedicalStore: Optional[MedicalStoreResponse] = Field(None, alias='store') # Expects a loaded Patient object


    model_config = ConfigDict(from_attributes=True)  
        


# -------------------------
# Bill + BillItem
# -------------------------

## Bill Item Schemas
# --------------------
class BillItemBase(BaseModel):
    product_id: str = Field(..., description="Product ID for this bill item")
    batch_no: str = Field(..., description="Batch number (alphanumeric)")
    expiry_date: date = Field(..., description="Expiry date of the product batch (YYYY-MM-DD)")
    quantity: int = Field(..., gt=0, description="Number of units sold")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    line_total: float = Field(..., ge=0, description="Total for this line item (quantity * unit_price)")


class BillItemCreate(BillItemBase):
    pass


class BillItemResp(BillItemBase):
    bill_item_id: str
    bill_id: str

    class Config:
        from_attributes = True

## Bill Schemas
# --------------
class BillCreate(BaseModel):
    # IDs are optional because the route logic will derive/validate them
    issuer_store_id: Optional[str] = Field(None, description="Store issuing the bill (optional, derived from user)")
    issuer_supplier_id: Optional[str] = Field(None, description="Supplier issuing the bill (optional, derived from user)")
    
    # Recipient: XOR enforced in route
    customer_id: Optional[str] = Field(None, description="Customer receiving the bill (must be exclusive with patient_id)")
    patient_id: Optional[str] = Field(None, description="Patient receiving the bill (must be exclusive with customer_id)")
    
    product_id: Optional[str] = Field(None, description="Optional single product reference for the Bill header")

    # Financials
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0)
    total_amount: float = Field(..., ge=0)

    items: List[BillItemCreate] = Field(default_factory=list, description="List of products included in this bill")


class BillResp(BillCreate):
    bill_id: str
    created_at: datetime
    # Ensures BillItemResp is used for nested items
    items: List[BillItemResp] = Field(default_factory=list)

    class Config:
        from_attributes = True
    
# -------------------------
# Supplier Product
# -------------------------
class ProductNested(BaseModel):
    generic_name: Optional[str]
    brand: Optional[str]
    dosage: Optional[str]
    form: Optional[str]
    category: Optional[str]
    image: Optional[str] = None
    image_mime: Optional[str] = None

    class Config:
        from_attributes = True

    # Automatically convert bytes -> base64 string
    @field_validator("image", mode="before")
    def encode_image(cls, v):
        if isinstance(v, (bytes, bytearray)):
            return base64.b64encode(v).decode("utf-8")
        return v

class SupplierNested(BaseModel):
    supplier_name: str

    class Config:
        from_attributes = True

class SupplierProductBase(BaseModel):
    supplier_sku: Optional[str] = None
    lead_time_days: Optional[int] = None
    price: Optional[condecimal(max_digits=18, decimal_places=2)] = None

class SupplierProductCreate(SupplierProductBase):
    product_id: UUID  # client must provide only product_id

class SupplierProductResponse(SupplierProductBase):
    supplier_product_id: UUID
    supplier_id: UUID
    product_id: UUID
    created_at: datetime
    product: ProductNested
    supplier: SupplierNested

    class Config:
        from_attributes = True

class SupplierProductByNameCreate(SupplierProductBase):
    name: str

    class Config:
        from_attributes = True

# -------------------------
# Store Settings
# -------------------------
class StoreSettingsCreate(BaseSchema):
    store_id: str
    accepts_online_orders: bool = True
    notif_on_low_stock: bool = True
    low_stock_threshold: int = 5

class StoreSettingsResp(StoreSettingsCreate):
    store_settings_id: str
    created_at: datetime
    class Config:
        from_attributes = True


# -------------------------
# Audit Log
# -------------------------
class AuditLogCreate(BaseSchema):
    store_id: str
    user_id: Optional[str] = None
    action: str
    details: Optional[str] = None

class AuditLogResp(AuditLogCreate):
    log_id: str
    timestamp: datetime
    class Config:
        from_attributes = True


# -------------------------
# Medical Store Dashboard
# -------------------------
class MedicalStoreDashboardResp(BaseSchema):
    dashboard_id: str
    store_id: str
    total_inventory_items: int
    total_products: int
    total_customers: int
    total_suppliers: int
    pending_requests: int
    last_updated: datetime

    class Config:
        from_attributes = True
# -------------------------
# Base Cart Item Schema
# -------------------------
class CartItemBase(BaseModel):
    product_id: str = Field(..., description="UUID of the product")
    quantity: int = Field(1, description="Number of units added to the cart")
    price: float = Field(..., description="Unit price of the product")
    subtotal: Optional[float] = None

    class Config:
        from_attributes = True  # Pydantic v2 ORM mode


# -------------------------
# Create Cart Item Schema
# -------------------------
class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1


# -------------------------
# Cart Item Response Schema
# -------------------------
class CartItemOut(CartItemBase):
    cart_item_id: str
    created_at: datetime


# -------------------------
# Base Cart Schema
# -------------------------
class CartBase(BaseModel):
    store_id: str
    user_id: Optional[str] = None

    class Config:
        from_attributes = True


# -------------------------
# Cart Creation Schema
# -------------------------
class CartCreate(BaseModel):
    store_id: str


# -------------------------
# Cart Response Schema
# -------------------------
class CartOut(BaseModel):
    cart_id: str
    store_id: str
    items: List[CartItemOut] = []
    total: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -------------------------
# Checkout Response Schema
# -------------------------
class CheckoutResponse(BaseModel):
    message: str
    bill_id: str
    total: float

#-----------------------------
# Orders
#-----------------------------

# -----------------------------
# 1. Schemas for Order Item Creation
# -----------------------------
class OrderItemCreate(BaseModel):
    # Use UUID for ID fields for strict validation
    product_id: UUID
    supplier_id: UUID
    quantity: int = Field(..., gt=0) # Ensure quantity is positive
    price: float = Field(..., ge=0)  # Ensure price is non-negative
    total_price: float = Field(..., ge=0)

# -----------------------------
# 2. Schemas for Order Creation
# -----------------------------
class OrderCreate(BaseModel):
    # Use UUID for ID fields for strict validation
    store_id: UUID
    supplier_id: UUID
    
    # order_date is typically set by the server, but kept optional for flexibility
    order_date: Optional[datetime] = None
    
    status: Optional[str] = "pending"
    # total_amount will be calculated by the backend in a production system, 
    # but based on your current model, we keep it as input.
    total_amount: float = Field(0, ge=0)
    
    # Items are required for a valid order, but set default for empty payload handling
    items: List[OrderItemCreate] = Field(default_factory=list)
    
    # Pydantic Configuration (Optional, but useful)
    class Config:
        json_encoders = {UUID: str}
        from_attributes = True

# -----------------------------
# 3. Schemas for Order Item Response
# -----------------------------
class OrderItemResp(OrderItemCreate):
    # IDs generated by the system should be UUIDs
    order_item_id: UUID
    order_id: UUID
    
    # Optionally add created_at/updated_at if OrderItem model has them
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Pydantic Configuration
    class Config:
        json_encoders = {UUID: str}
        from_attributes = True

# -----------------------------
# 4. Schemas for Order Response
# -----------------------------
class OrderResp(BaseModel):
    # IDs generated by the system should be UUIDs
    order_id: UUID
    store_id: UUID
    supplier_id: UUID
    
    order_date: Optional[datetime]
    status: str
    total_amount: float
    
    created_at: datetime
    updated_at: datetime
    
    # The nested relationship must be a List of the response schema
    items: List[OrderItemResp] = Field(default_factory=list)
    
    # Pydantic Configuration
    class Config:
        # Crucial for SQLAlchemy object conversion and nested relationship loading
        json_encoders = {UUID: str}
        from_attributes = True

# ---------------------------
# ENUM for Subscription Status
# ---------------------------
class SubscriptionStatus(str, Enum):
    created = "created"
    active = "active"
    cancelled = "cancelled"
    expired = "expired"


# ---------------------------
# PLAN SCHEMAS
# ---------------------------
class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float
    interval: str = "month"
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanOut(PlanBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------
# SUBSCRIPTION SCHEMAS
# ---------------------------
class SubscriptionBase(BaseModel):
    plan_id: UUID
    razorpay_subscription_id: str
    razorpay_plan_id: str
    status: Optional[SubscriptionStatus] = SubscriptionStatus.created
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    user_id: UUID


class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    cancelled_at: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionOut(SubscriptionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# -----------------------------
# Payment Response
# -----------------------------

# -----------------------------
# Create Razorpay Order Request
# -----------------------------
class CreateOrderRequest(BaseModel):
    bill_id: Optional[UUID4] = None
    store_id: Optional[UUID4] = None
    customer_id: Optional[UUID4] = None
    amount: float
    currency: str = "INR"
    description: Optional[str] = None


# -----------------------------
# Razorpay Order Response
# -----------------------------
class RazorpayOrderResponse(BaseModel):
    id: str
    amount: float
    currency: str
    status: str
    key: str


# -----------------------------
# Verify Payment Request
# -----------------------------
class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# -----------------------------
# Payment Success Response
# -----------------------------
class PaymentSuccessResponse(BaseModel):
    success: bool
    message: str
