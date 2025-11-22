# routers/store.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, BackgroundTasks, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from fastapi_pagination import Page, paginate
from fastapi.encoders import jsonable_encoder
from geopy.geocoders import Nominatim
from fastapi.responses import StreamingResponse
from math import radians, cos, sin, asin, sqrt
import os
import uuid
import traceback
import base64
from typing import List, Optional
from pathlib import Path
from io import BytesIO

from database import get_db
from models import *
from schemas import *
from utils.token_utils import  role_required, RoleEnum, get_current_user, decode_access_token
import logging
logger = logging.getLogger(__name__)
CurrentUser = Annotated[dict, Depends(role_required(RoleEnum.CHEMIST))]


router = APIRouter()

# Define a storage location (adjust as needed for your system)
PRESCRIPTION_FILE_DIR = Path("path/to/your/prescription/files") 

# Utility: Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    Returns distance in KM.
    """
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def try_geocode(geolocator, address_variants):
    """Try multiple address variants until one works"""
    for addr in address_variants:
        if addr.strip():
            location = geolocator.geocode(addr, timeout=5)
            if location:
                return location
    return None

def encode_binary_field(binary_data: Optional[bytes]) -> Optional[str]:
    if binary_data:
        return base64.b64encode(binary_data).decode('utf-8')
    return None

def validate_uuid(value: Optional[str], field_name: str) -> Optional[str]:
    """Ensure the value is a valid UUID string or None."""
    if not value:
        return None
    try:
        return str(UUID(value))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a valid UUID.")


# -------------------------
# CREATE Store (Protected - Only CHEMIST)
# -------------------------
@router.post("/register", response_model=MedicalStoreCreateSuccess, status_code=status.HTTP_201_CREATED)
async def create_medical_store(
    store_name: str = Form(...),
    owner_name: str = Form(...),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    store_type: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    locality: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    phone: str = Form(...),
    open_hours: Optional[str] = Form(None),
    delivery_radius_km: Optional[int] = Form(None),
    license_document: Optional[UploadFile] = File(None),
    store_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    store_id = str(uuid.uuid4())

    # Owner Validation
    if owner_name.strip().lower() != current_user.username.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner name does not match your account information."
        )

    # Duplicate checks before costly operations
    if db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already registered a Medical Store."
        )
    if db.query(MedicalStore).filter(MedicalStore.store_name == store_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A store with the name '{store_name}' is already registered."
        )
    if db.query(MedicalStore).filter(MedicalStore.phone == phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A store with the phone number '{phone}' is already registered."
        )

    # Geocode address
    full_address = f"{address or ''}, {locality or ''}, {city or ''}, {pin_code or ''}"
    geolocator = Nominatim(user_agent="medical_store_app")
    location = try_geocode(geolocator, [
        full_address,
        f"{locality or ''}, {city or ''}, {pin_code or ''}",
        f"{city or ''}, {pin_code or ''}"
    ])
    latitude, longitude = (location.latitude, location.longitude) if location else (None, None)

    try:
        # Read files before adding to DB to avoid exceptions post commit
        license_doc_bytes = await license_document.read() if license_document else None
        license_mime = license_document.content_type if license_document else None

        store_photo_bytes = await store_photo.read() if store_photo else None
        photo_mime = store_photo.content_type if store_photo else None

        new_store = MedicalStore(
            store_id=store_id,
            store_name=store_name,
            owner_id=str(current_user.id),
            owner_name=owner_name,
            age=age,
            gender=gender,
            store_type=store_type,
            address=address,
            city=city,
            locality=locality,
            pin_code=pin_code,
            phone=phone,
            email=current_user.email,
            open_hours=open_hours,
            delivery_radius_km=delivery_radius_km,
            latitude=latitude,
            longitude=longitude,
            license_document=license_doc_bytes,
            license_mime=license_mime,
            store_photo=store_photo_bytes,
            photo_mime=photo_mime,
            created_at=datetime.utcnow(),
        )
        db.add(new_store)
        db.commit()
        db.refresh(new_store)

        store_response = MedicalStoreResponse(
            store_id=new_store.store_id,
            store_name=new_store.store_name,
            owner_id=new_store.owner_id,
            owner_name=new_store.owner_name,
            age=new_store.age,
            gender=new_store.gender,
            store_type=new_store.store_type,
            address=new_store.address,
            city=new_store.city,
            locality=new_store.locality,
            pin_code=new_store.pin_code,
            phone=new_store.phone,
            email=new_store.email,
            open_hours=new_store.open_hours,
            delivery_radius_km=new_store.delivery_radius_km,
            latitude=new_store.latitude,
            longitude=new_store.longitude,
            created_at=new_store.created_at,
        )

        return MedicalStoreCreateSuccess(
            message="Medical Store registered successfully.",
            store=store_response
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error while creating Medical Store: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while creating Medical Store. Please try again."
        )


# -------------------------
# READ: Get all stores (Public + Search + Medicine Availability)
# -------------------------
@router.get("/get_all_store/", response_model=List[MedicalStoreResponse])
def get_all_stores(
    owner_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    locality: Optional[str] = Query(None),
    pin_code: Optional[str] = Query(None),
    medicine: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(5, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(MedicalStore)

        if owner_name:
            query = query.filter(MedicalStore.owner_name.ilike(f"%{owner_name}%"))
        if search:
            query = query.filter(MedicalStore.store_name.ilike(f"%{search}%"))
        if city:
            query = query.filter(MedicalStore.city.ilike(f"%{city}%"))
        if locality:
            query = query.filter(MedicalStore.locality.ilike(f"%{locality}%"))
        if pin_code:
            query = query.filter(MedicalStore.pin_code == pin_code)
        if medicine:
            query = query.join(MedicalStore.inventories).filter(
                Inventory.product_name.ilike(f"%{medicine}%")
            ).distinct()

        stores = query.all()
    except SQLAlchemyError as db_exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(db_exc)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query input: {str(exc)}"
        )

    if latitude is not None and longitude is not None:
        try:
            nearby_stores = []
            for store in stores:
                if store.latitude is not None and store.longitude is not None:
                    distance = haversine(latitude, longitude, store.latitude, store.longitude)
                    if distance <= radius_km:
                        nearby_stores.append(store)
            stores = nearby_stores
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error in geo-filtering: {str(exc)}"
            )

    if not stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No medical stores found for the given criteria."
        )

    response = []
    for store in stores[skip: skip + limit]:
        try:
            response.append(
                MedicalStoreResponse(
                    store_id=store.store_id,
                    owner_id=store.owner_id,
                    store_name=store.store_name,
                    owner_name=store.owner_name,
                    age=store.age,
                    gender=store.gender,
                    store_type=store.store_type,
                    address=store.address,
                    city=store.city,
                    locality=store.locality,
                    pin_code=store.pin_code,
                    phone=store.phone,
                    email=store.email,
                    open_hours=store.open_hours,
                    delivery_radius_km=store.delivery_radius_km,
                    latitude=store.latitude,
                    longitude=store.longitude,
                    created_at=store.created_at,
                    store_photo=base64.b64encode(store.store_photo).decode("utf-8") if store.store_photo else None,
                    photo_mime=store.photo_mime
                )
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize store data: {str(exc)}"
            )
    return response

# -------------------------
# GET: My Store (Chemist only)
# -------------------------
@router.get("/me", response_model=MedicalStoreResponse)
def get_my_store(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found for current user")
    
    return MedicalStoreResponse(
        store_id=store.store_id,
        store_name=store.store_name,
        owner_id=store.owner_id,
        owner_name=store.owner_name,
        age=store.age,
        gender=store.gender,
        store_type=store.store_type,
        license_document=encode_binary_field(store.license_document),
        license_mime=store.license_mime,
        store_photo=encode_binary_field(store.store_photo),
        photo_mime=store.photo_mime,
        address=store.address,
        city=store.city,
        locality=store.locality,
        pin_code=store.pin_code,
        phone=store.phone,
        email=store.email,
        open_hours=store.open_hours,
        delivery_radius_km=store.delivery_radius_km,
        latitude=store.latitude,
        longitude=store.longitude,
        created_at=store.created_at,
    )

# -------------------------
# UPDATE: My Store (Chemist only)
# -------------------------
@router.put("/update", response_model=MedicalStoreUpdate)
async def update_my_store(
    store_name: Optional[str] = Form(None),
    owner_name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),  # "Male", "Female", "Other"
    store_type: Optional[str] = Form(None),  # e.g. "Chemist", "Pharmacy"
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    locality: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    open_hours: Optional[str] = Form(None),
    delivery_radius_km: Optional[int] = Form(None),
    license_document: Optional[UploadFile] = File(None),  # Re-upload allowed
    store_photo: Optional[UploadFile] = File(None),       # Re-upload allowed
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    try:
        # Update text fields
        if store_name is not None:
            store.store_name = store_name
        if owner_name is not None:
            store.owner_name = owner_name
        if age is not None:
            if age < 18 or age > 100:
                raise HTTPException(status_code=400, detail="Age must be between 18 and 100")
            store.age = age
        if gender is not None:
            gender_norm = gender.strip().capitalize()
            if gender_norm not in ["Male", "Female", "Other"]:
                raise HTTPException(status_code=400, detail="Gender must be 'Male', 'Female', or 'Other'")
            store.gender = gender_norm
        if store_type is not None:
            allowed_store_types = {"chemist", "all", "pharmacy", "medical", "drugstore"}
            if store_type.strip().lower() not in allowed_store_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Store type must be one of {', '.join([t.capitalize() for t in allowed_store_types])}"
                )
            store.store_type = store_type.strip().capitalize()
        if address is not None:
            store.address = address
        if city is not None:
            store.city = city
        if locality is not None:
            store.locality = locality
        if pin_code is not None:
            store.pin_code = pin_code
        if phone is not None:
            if not (len(phone) == 10 and phone.isdigit() and phone[0] in "6789"):
                raise HTTPException(status_code=400, detail="Phone must be a valid 10-digit Indian number starting with 6/7/8/9")
            store.phone = phone
        if open_hours is not None:
            store.open_hours = open_hours
        if delivery_radius_km is not None:
            if delivery_radius_km < 0:
                raise HTTPException(status_code=400, detail="Delivery radius cannot be negative")
            store.delivery_radius_km = delivery_radius_km

        # Validate and update the files
        if license_document is not None:
            store.license_document = await license_document.read()
            store.license_mime = license_document.content_type

        if store_photo is not None:
            store.store_photo = await store_photo.read()
            store.photo_mime = store_photo.content_type

        # Require at least one upload existing
        if not store.license_document or not store.store_photo:
            raise HTTPException(status_code=400, detail="Both license document and store photo are required at least once")

        # Commit to DB
        db.commit()
        db.refresh(store)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_detail = traceback.format_exc()
        print("Update Error Traceback:", error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the store: {str(e)}"
        )

    # Encode binary fields before returning
    return MedicalStoreUpdate(
        store_id=store.store_id,
        store_name=store.store_name,
        owner_id=store.owner_id,
        owner_name=store.owner_name,
        age=store.age,
        gender=store.gender,
        store_type=store.store_type,
        license_document=encode_binary_field(store.license_document),
        license_mime=store.license_mime,
        store_photo=encode_binary_field(store.store_photo),
        photo_mime=store.photo_mime,
        address=store.address,
        city=store.city,
        locality=store.locality,
        pin_code=store.pin_code,
        phone=store.phone,
        email=store.email,
        open_hours=store.open_hours,
        delivery_radius_km=store.delivery_radius_km,
        latitude=store.latitude,
        longitude=store.longitude,
        created_at=store.created_at
    )    
# -------------------------
# GET: Store by ID (Public)
# -------------------------
@router.get("/{store_id}", response_model=MedicalStoreResponse)
def get_store_by_id(store_id: UUID, db: Session = Depends(get_db)):
    store = db.query(MedicalStore).filter(MedicalStore.store_id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

# -------------------------
# DELETE Own Store (Chemist)
# -------------------------
@router.delete("/delete_me")
def delete_my_store(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST)),
):
    try:
        # 🔹 Find the store of the current chemist
        store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
        if not store:
            raise HTTPException(status_code=404, detail="No store found for this chemist")

        db.delete(store)
        db.commit()
        return {"message": "Store deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while deleting store: {str(e)}"
        )

# ------------------------
# Add Inventory (With Full Product Info From Form)
# ------------------------
@router.post("/inventory/add", response_model=InventoryResponse)
def add_inventory(
    product_name: str = Form(...),
    brand: str = Form(...),
    dosage: str = Form(...),
    form: str = Form(...),
    category: str = Form(...),
    batch_no: str = Form(...),
    expiry_date: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    store_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Convert expiry string to datetime
        expiry_dt = datetime.fromisoformat(expiry_date)

        # ============================
        # 1. FIND STORE (LOGICALLY CORRECT)
        # ============================
        if current_user.role == RoleEnum.CHEMIST:
            store = db.query(MedicalStore).filter(
                MedicalStore.owner_id == str(current_user.id)
            ).first()
            if not store:
                raise HTTPException(status_code=404, detail="Store not found for this chemist")

        elif current_user.role == RoleEnum.ADMIN:
            if not store_id:
                raise HTTPException(status_code=400, detail="store_id required for admin")
            store = db.query(MedicalStore).filter(
                MedicalStore.store_id == store_id
            ).first()
            if not store:
                raise HTTPException(status_code=404, detail="Store not found")

        else:
            raise HTTPException(status_code=403, detail="Unauthorized role")


        # ============================
        # 2. CHECK IF PRODUCT EXISTS
        # ============================
        product = db.query(Product).filter(
            Product.name == product_name,
            Product.brand == brand,
            Product.dosage == dosage,
            Product.form == form,
            Product.category == category
        ).first()

        # If product does not exist → create automatically
        if not product:
            product = Product(
                product_id=str(uuid.uuid4()),
                name=product_name,
                brand=brand,
                dosage=dosage,
                form=form_value,
                category=category
            )
            db.add(product)
            db.commit()
            db.refresh(product)


        # ============================
        # 3. CHECK IF SAME BATCH EXISTS
        # ============================
        existing_batch = db.query(Inventory).filter(
            Inventory.product_id == product.product_id,
            Inventory.store_id == store.store_id,
            Inventory.batch_no == batch_no
        ).first()

        if existing_batch:

            # A. Expiry must match
            if existing_batch.expiry_date != expiry_dt:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expiry mismatch: Existing batch has expiry {existing_batch.expiry_date.date()}."
                )

            # B. Price must match
            if float(existing_batch.price) != float(price):
                raise HTTPException(
                    status_code=400,
                    detail=f"Price mismatch: Existing batch price is {existing_batch.price}."
                )

            # C. Add quantity (merge stock)
            existing_batch.quantity += quantity
            existing_batch.last_updated = datetime.utcnow()

            db.commit()
            db.refresh(existing_batch)
            return existing_batch


        # ============================
        # 4. CREATE NEW INVENTORY ENTRY
        # ============================
        new_inv = Inventory(
            inventory_id=str(uuid.uuid4()),
            store_id=store.store_id,
            product_id=product.product_id,
            product_name=product.name,
            batch_no=batch_no,
            expiry_date=expiry_dt,
            quantity=quantity,
            price=price
        )

        db.add(new_inv)
        db.commit()
        db.refresh(new_inv)

        # ============================
        # 5. Response
        # ============================
        return InventoryResponse(
            inventory_id=new_inv.inventory_id,
            store_id=new_inv.store_id,
            product_id=new_inv.product_id,
            product_name=new_inv.product_name,
            batch_no=new_inv.batch_no,
            expiry_date=new_inv.expiry_date,
            quantity=new_inv.quantity,
            price=new_inv.price,
            created_at=new_inv.created_at,
            last_updated=new_inv.last_updated,
            product=ProductNested(
                brand=product.brand,
                generic_name=getattr(product, "generic_name", None),
                dosage=product.dosage,
                form=product.form,
                category=product.category
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Error in add_inventory:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Get ALL inventory for all stores owned by chemist
# -------------------------
@router.get("/inventory/all", response_model=List[InventoryResponse])
def get_all_inventory(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST)),
):
    if current_user.role != RoleEnum.CHEMIST:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    stores = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).all()
    if not stores:
        return []

    store_ids = [str(store.store_id) for store in stores if store.store_id]
    if not store_ids:
        return []

    inventory_items = (
        db.query(Inventory)
        .options(joinedload(Inventory.product))  # eager load product
        .filter(Inventory.store_id.in_(store_ids))
        .all()
    )

    return inventory_items or []

# -------------------------
# Search Inventory (with multiple dynamic filters)
# -------------------------
@router.get("/inventory/search", response_model=List[InventoryResponse])
def search_inventory(
    product_name: Optional[str] = None,
    batch_no: Optional[str] = None,
    expiry_before: Optional[datetime] = None,
    brand: Optional[str] = None,
    generic_name: Optional[str] = None,
    dosage: Optional[str] = None,
    form: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(role_required([RoleEnum.CHEMIST])),
):
    try:
        user_id = str(current_user.id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Get all stores owned by the current user
    stores = db.query(MedicalStore).filter(MedicalStore.owner_id == user_id).all()
    if not stores:
        raise HTTPException(status_code=404, detail="No stores found for the user")

    store_ids = [str(store.store_id) for store in stores]

    # Base query: Inventory joined with Product
    query = db.query(Inventory).join(Product, Inventory.product_id == Product.product_id).filter(
        Inventory.store_id.in_(store_ids)
    )

    # Apply dynamic filters
    if product_name:
        query = query.filter(Product.name.ilike(f"%{product_name}%"))
    if batch_no:
        query = query.filter(Inventory.batch_no.ilike(f"%{batch_no}%"))
    if expiry_before:
        query = query.filter(Inventory.expiry_date <= expiry_before)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if generic_name:
        query = query.filter(Product.generic_name.ilike(f"%{generic_name}%"))
    if dosage:
        query = query.filter(Product.dosage.ilike(f"%{dosage}%"))
    if form:
        query = query.filter(Product.form.ilike(f"%{form}%"))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No inventory items matched the criteria")

    # Build InventoryResponse with nested product
    response = []
    for inv in results:
        response.append(
            InventoryResponse(
                inventory_id=inv.inventory_id,
                store_id=inv.store_id,
                product_id=inv.product_id,
                product_name=inv.product_name,
                batch_no=inv.batch_no,
                expiry_date=inv.expiry_date,
                quantity=inv.quantity,
                price=inv.price,
                created_at=inv.created_at,
                last_updated=inv.last_updated,
                product=ProductNested(
                    brand=inv.product.brand,
                    generic_name=getattr(inv.product, "generic_name", None),
                    dosage=getattr(inv.product, "dosage", None),
                    form=getattr(inv.product, "form", None),
                    category=getattr(inv.product, "category", None)
                )
            )
        )

    return response

# -------------------------
# Update Inventory
# -------------------------
@router.put("/inventory/update", response_model=InventoryResponse)
async def update_inventory_by_name_brand(
    product_name: str = Form(...),
    brand: str = Form(...),
    batch_no: str = Form(...),
    expiry_date: datetime = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),   # optional re-upload
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST)),
):
    # 1. Find store owned by this chemist
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="No store found for this chemist")

    # 2. Find product by name + brand
    product = (
        db.query(Product)
        .filter(Product.name == product_name, Product.brand == brand)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product '{product_name}' with brand '{brand}' not found"
        )

    # 3. Find inventory entry for this store + product
    inv = (
        db.query(Inventory)
        .filter(
            Inventory.store_id == store.store_id,
            Inventory.product_id == product.product_id,
        )
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory entry not found")

    # 4. Update fields
    inv.batch_no = batch_no
    inv.expiry_date = expiry_date
    inv.quantity = quantity
    inv.price = price
    inv.last_updated = datetime.utcnow()

    # 5. Handle optional image re-upload - save actual binary content
    if image:
        # For asynchronous read, awaiting is needed; if not async, use image.file.read()
        file_bytes = await image.read()
        product.image = file_bytes
        product.image_mime = image.content_type

    # 6. Save changes
    db.commit()
    db.refresh(inv)

    return inv

# -------------------------
# Delete Inventory
# -------------------------
@router.delete("/inventory/delete")
def delete_inventory(
    product_name: str = Query(...),
    brand: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    # Find the chemist owned store
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="No store found for this chemist")

    # Find product by name and brand
    product = db.query(Product).filter(Product.name == product_name, Product.brand == brand).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Find inventory entry for store + product
    inv = db.query(Inventory).filter(
        Inventory.store_id == store.store_id,
        Inventory.product_id == product.product_id,
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Inventory entry not found")

    # Delete inventory
    db.delete(inv)
    db.commit()
    return {"message": "Inventory item deleted successfully"}

# -------------------------
# Link Supplieer To Medical Store
# -------------------------

@router.post("/supplier/link/{supplier_id}", response_model=SupplierResponse)
def link_supplier_to_store(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    """
    Link an existing supplier to the chemist's store.
    """

    # Find store owned by current chemist
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Find existing supplier
    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Link supplier to this store (update store_id)
    supplier.store_id = store.store_id
    db.commit()
    db.refresh(supplier)

    return supplier


# -------------------------------------END THE MEDICAL STORE ROUTES-----------------------------------





# -------------------------------------
# MEDICAL STORE ROUTES - ORGANIZED
# -------------------------------------

# ========= SUPPLIER ROUTES =========

# Supplier Registration (Conditional store linking)
@router.post("/supplier", response_model=SupplierResponse)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.SUPPLIER, RoleEnum.CHEMIST))
):
    """
    Register a supplier.
    - If CHEMIST registers → supplier linked to chemist's store_id.
    - If SUPPLIER registers → not linked to any store (store_id=None).
    """

    # 1. Check for duplicate supplier by phone or email ONLY inside Supplier table
    existing_supplier = db.query(Supplier).filter(
        (Supplier.phone == supplier.phone) |
        (Supplier.email == supplier.email) 
    ).first()

    if existing_supplier:
        raise HTTPException(
            status_code=400,
            detail="Supplier with this phone or email already exists."
        )

    # 2. Determine store_id based on role
    store_id = None
    if current_user.role == RoleEnum.CHEMIST:
        chemist_store = db.query(MedicalStore).filter(
            MedicalStore.owner_id == current_user.id
        ).first()
        if not chemist_store:
            raise HTTPException(
                status_code=400,
                detail="Chemist does not own any store to link the supplier."
            )
        store_id = chemist_store.store_id

    # 3. Create Supplier
    new_supplier = Supplier(
        supplier_id=str(current_user.id),
        supplier_name=current_user.username,
        contact_name=supplier.contact_name,
        phone=supplier.phone,
        email=supplier.email,               # <-- IMPORTANT: use supplier.email, not current_user.email
        address=supplier.address,
        city=supplier.city,
        pin_code=supplier.pin_code,
        age=supplier.age,
        gender=supplier.gender.lower() if supplier.gender else None,
        created_at=datetime.utcnow(),
        store_id=store_id,
        created_by=current_user.id
    )

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier


# Get All Suppliers
@router.get("/supplier/get_all_suppliers", response_model=List[SupplierResponse])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.SUPPLIER,RoleEnum.CHEMIST))
):
    suppliers = db.query(Supplier).all()
    return suppliers

# Get Supplier by ID
@router.get("/supplier/me", response_model=SupplierResponse)
def get_my_supplier(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.SUPPLIER))
):
    supplier = db.query(Supplier).filter(
        Supplier.user_id == current_user["user_id"]
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier for this user not found")
    
    return supplier


# Search suppliers linked to store with filters
@router.get("/stores/suppliers/search", response_model=Page[SupplierResponse])
def search_store_suppliers(
    supplier_name: Optional[str] = Query(None),
    contact_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    pin_code: Optional[str] = Query(None),
    address: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None, description="Filter by product supplied"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.CHEMIST))
):
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == str(current_user.id)).first()
    if not store:
        raise HTTPException(status_code=403, detail="You don't own a medical store")
    inventory_products_subq = (
        db.query(Inventory.product_id)
        .filter(Inventory.store_id == store.store_id)
        .subquery()
    )
    query = db.query(Supplier).join(
        SupplierProduct, Supplier.supplier_id == SupplierProduct.supplier_id
    ).filter(
        SupplierProduct.product_id.in_(inventory_products_subq)
    )
    if product_name:
        query = query.join(Product, SupplierProduct.product_id == Product.product_id)\
                     .filter(Product.name.ilike(f"%{product_name}%"))
    if supplier_name:
        query = query.filter(Supplier.supplier_name.ilike(f"%{supplier_name}%"))
    if contact_name:
        query = query.filter(Supplier.contact_name.ilike(f"%{contact_name}%"))
    if phone:
        query = query.filter(Supplier.phone.ilike(f"%{phone}%"))
    if email:
        query = query.filter(Supplier.email.ilike(f"%{email}%"))
    if city:
        query = query.filter(Supplier.city.ilike(f"%{city}%"))
    if pin_code:
        query = query.filter(Supplier.pin_code.ilike(f"%{pin_code}%"))
    if address:
        query = query.filter(Supplier.address.ilike(f"%{address}%"))
    query = query.distinct()
    suppliers = query.all()
    return paginate(suppliers)

# Update Supplier (role-based)
@router.put("/supplier/update/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: object = Depends(role_required(RoleEnum.SUPPLIER, RoleEnum.CHEMIST)),
):
    """
    Update supplier with proper role-based authorization.
    - SUPPLIER: can update only their own supplier account.
    - CHEMIST: can update suppliers they created or linked to their store.
    """
    user_id = str(getattr(current_user, "id", None)).lower()
    current_role = getattr(current_user, "role", None)
    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier_created_by = str(supplier.created_by).lower()
    if current_role == RoleEnum.SUPPLIER:
        if supplier_created_by != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own supplier account."
            )
    elif current_role == RoleEnum.CHEMIST:
        chemist_store = db.query(MedicalStore).filter(MedicalStore.owner_id == user_id).first()
        if not chemist_store:
            raise HTTPException(status_code=400, detail="Chemist does not own any store.")
        if supplier_created_by == user_id:
            pass  # Full update allowed
        elif supplier.store_id == chemist_store.store_id:
            update_data = supplier_update.dict(exclude_unset=True)
            allowed_fields = {"store_id"}
            for field in update_data.keys():
                if field not in allowed_fields:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Cannot update {field} for this supplier."
                    )
        else:
            raise HTTPException(
                status_code=403,
                detail="Supplier is not linked to your store or created by you."
            )
    update_data = supplier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier

# Delete Supplier (role-based behavior)
@router.delete("/supplier/{supplier_id}")
def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: object = Depends(role_required(RoleEnum.SUPPLIER, RoleEnum.CHEMIST))
):
    """
    Delete supplier with correct role logic:
    - SUPPLIER → can delete ONLY their own supplier account.
    - CHEMIST → can only unlink supplier from their store.
    """
    # Validate UUID
    try:
        supplier_uuid = uuid.UUID(supplier_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid supplier ID.")

    # Load supplier
    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_uuid).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # =========================================================
    # CASE 1: SUPPLIER → Delete their own supplier profile
    # =========================================================
    if current_user.role == RoleEnum.SUPPLIER:
        # A supplier can delete ONLY their own supplier record
        if supplier.email != current_user.email and supplier.created_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can delete only your own supplier account."
            )

        db.delete(supplier)
        db.commit()
        return {"message": "Supplier account deleted successfully."}

    # =========================================================
    # CASE 2: CHEMIST → Unlink supplier from chemist's store only
    # =========================================================
    if current_user.role == RoleEnum.CHEMIST:
        chemist_store = (
            db.query(MedicalStore)
            .filter(MedicalStore.owner_id == current_user.id)
            .first()
        )

        if not chemist_store:
            raise HTTPException(
                status_code=400,
                detail="You do not own any store."
            )

        # Ensure supplier is linked to this chemist’s store
        if supplier.store_id != chemist_store.store_id:
            raise HTTPException(
                status_code=403,
                detail="This supplier is not linked to your store."
            )

        # Unlink the supplier (do NOT delete)
        supplier.store_id = None
        db.commit()
        return {"message": "Supplier unlinked from store successfully."}

    
# ========= PRODUCT ROUTES =========

# Create Global Product
@router.post("/products", response_model=ProductResponse)
async def create_product(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.CHEMIST])),
    name: str = Form(None),
    brand: str = Form(None),
    generic_name: str = Form(None),
    dosage: str = Form(None),
    form: str = Form(None),
    category: str = Form(None),
    hsn_code: str = Form(None),
    image: UploadFile = File(None),
):
    try:
        # Parse data depending on content type
        if request.headers.get("content-type", "").startswith("multipart"):
            product_data = {
                "name": name,
                "brand": brand,
                "generic_name": generic_name,
                "dosage": dosage,
                "form": form,
                "category": category,
                "hsn_code": hsn_code,
            }
        else:
            body = await request.json()
            product_data = ProductCreate(**body).dict()

        # Query existing products with the same name
        existing_products = db.query(Product).filter(
            Product.name.ilike(product_data["name"])
        ).all()

        # Check against all existing products with this name to enforce your logic
        for existing in existing_products:
            # Compare fields excluding hsn_code
            fields_match = (
                (existing.brand or "") == (product_data.get("brand") or "") and
                (existing.generic_name or "") == (product_data.get("generic_name") or "") and
                (existing.dosage or "") == (product_data.get("dosage") or "") and
                (existing.form or "") == (product_data.get("form") or "") and
                (existing.category or "") == (product_data.get("category") or "")
            )
            if fields_match:
                # If fields match but hsn_code differs or matches, reject creation
                if (existing.hsn_code or "") != (product_data.get("hsn_code") or ""):
                    raise HTTPException(status_code=409, detail="Product already exists with different HSN code")
                else:
                    raise HTTPException(status_code=409, detail="Product already exists")

        # Image processing
        image_bytes, image_mime = None, None
        if image:
            image_bytes = await image.read()
            image_mime = image.content_type

        # Create new product
        new_product = Product(
            product_id=str(uuid.uuid4()),
            name=product_data["name"],
            brand=product_data.get("brand"),
            generic_name=product_data.get("generic_name"),
            dosage=product_data.get("dosage"),
            form=product_data.get("form"),
            category=product_data.get("category"),
            hsn_code=product_data.get("hsn_code"),
            image=image_bytes,
            image_mime=image_mime,
            created_at=datetime.utcnow(),
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except HTTPException:
        raise  # propagate HTTPExceptions
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create product: {str(e)}")

# ---------------------------
# ✅ Get All Products (Safe + Always Responds)
# ---------------------------
@router.get("/product/get_all_products", response_model=List[ProductResponse])
def get_all_products(
    db: Session = Depends(get_db),
    current_user=Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.CHEMIST]))
):
    try:
        products = db.query(Product).all()
        if not products:
            # Return an empty list instead of failing silently
            return []
        return products

    except Exception as e:
        # This prevents "ERR_EMPTY_RESPONSE" and gives a clear message
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving products: {str(e)}"
        )


# Get product by name (case-insensitive)
@router.get("/products/name/{name}", response_model=ProductResponse)
def get_product_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user=Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.CHEMIST]))
):
    product = db.query(Product).filter(Product.name.ilike(name)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ---------------------------
# Update Product
# ---------------------------
@router.put("/product-update/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    generic_name: Optional[str] = Form(None),
    dosage: Optional[str] = Form(None),
    form_: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    hsn_code: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.CHEMIST]))
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update fields if provided
    if name: product.name = name
    if brand: product.brand = brand
    if generic_name: product.generic_name = generic_name
    if dosage: product.dosage = dosage
    if form_: product.form = form_
    if category: product.category = category
    if hsn_code: product.hsn_code = hsn_code

    # Update image if new one provided
    if image:
        product.image = await image.read()
        product.image_mime = image.content_type

    db.commit()
    db.refresh(product)
    return product
 
# ---------------------------
# Delete Product
# ---------------------------
@router.delete("/product_delete/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Manually delete related BillItems if needed
    bill_items = db.query(BillItem).filter(BillItem.product_id == product_id).all()
    for item in bill_items:
        db.delete(item)

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# -----------------------------------------------------
# Link Product to Supplier by Detailed Match and Expiry
# -----------------------------------------------------
@router.post("/supplier/products/link-detailed", response_model=SupplierProductResponse)
def link_supplier_product_detailed(
    data: SupplierProductLinkCreate,
    db: Session = Depends(get_db),
    current_user: object = Depends(role_required(RoleEnum.SUPPLIER))
):
    """
    Links a global product to the current supplier using detailed product fields 
    (dosage, brand, form, category) for accurate matching, and records the 
    latest batch expiry date.
    """
    try:
        # 1. Find the current Supplier record
        supplier = (
            db.query(Supplier)
            .filter(Supplier.email == current_user.email)
            .first()
        )
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier record not found. Please complete supplier profile.")

        # 2. Build the Product matching query (Case-insensitive check for all details)
        product_query = db.query(Product).filter(
            func.lower(Product.name) == func.lower(data.name.strip())
        )

        # Conditionally add filters for the optional fields for a strict match
        if data.dosage is not None:
            product_query = product_query.filter(func.lower(Product.dosage) == func.lower(data.dosage.strip()))
        
        if data.brand is not None:
            product_query = product_query.filter(func.lower(Product.brand) == func.lower(data.brand.strip()))
        
        if data.form is not None:
            product_query = product_query.filter(func.lower(Product.form) == func.lower(data.form.strip()))
            
        if data.category is not None:
            product_query = product_query.filter(func.lower(Product.category) == func.lower(data.category.strip()))

        product = product_query.first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found with the specified details.")

        # 3. Check for existing link (to prevent 400 Conflict)
        existing_link = (
            db.query(SupplierProduct)
            .filter(
                SupplierProduct.supplier_id == supplier.supplier_id,
                SupplierProduct.product_id == product.product_id,
            )
            .first()
        )
        if existing_link:
            raise HTTPException(status_code=400, detail="Product is already linked to this supplier.")

        # 4. Create the new SupplierProduct link
        new_link = SupplierProduct(
            # Assuming SupplierProduct ID is handled by SQLAlchemy defaults/triggers
            supplier_id=supplier.supplier_id,
            product_id=product.product_id,
            supplier_sku=data.supplier_sku,
            price=data.price,
            lead_time_days=data.lead_time_days,
            # ✅ NEW: Save the expiry date
            latest_expiry_date=data.latest_expiry_date, 
            created_at=datetime.utcnow(),
        )
        
        db.add(new_link)
        db.commit()
        
        # 5. Eager load and return the result for Pydantic validation
        fully_loaded_link = (
            db.query(SupplierProduct)
            .options(
                joinedload(SupplierProduct.product),
                joinedload(SupplierProduct.supplier)
            )
            .filter(SupplierProduct.supplier_product_id == new_link.supplier_product_id)
            .first()
        )
        
        if not fully_loaded_link:
             raise HTTPException(status_code=500, detail="Failed to retrieve linked record after creation.") 

        return fully_loaded_link
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback() 
        import traceback
        print("Error in link_supplier_product_detailed route:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
# List Of The Supplier Products
@router.get("/suppliers/products", response_model=List[SupplierProductResponse])
def get_supplier_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.CHEMIST])),
    # For Chemist, allow supplier_id to be passed as a query parameter
    supplier_id_param: Optional[str] = Query(None, alias="supplier_id")
):
    """
    Retrieves a list of products offered by a supplier.
    - SUPPLIER: ID is pulled from their user record.
    - CHEMIST: ID must be passed via the 'supplier_id' query parameter.
    """
    actual_supplier_id = None

    if current_user.role == RoleEnum.SUPPLIER:
        # Safely attempt to get supplier_id from the User object for the SUPPLIER role.
        # This prevents the AttributeError if the attribute is missing.
        actual_supplier_id = getattr(current_user, 'supplier_id', None)

        if not actual_supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier ID missing in user record. Please check user setup."
            )

    elif current_user.role == RoleEnum.CHEMIST:
        # For the CHEMIST role, the ID MUST come from the query parameter.
        actual_supplier_id = supplier_id_param

        if not actual_supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chemist must provide a 'supplier_id' query parameter to fetch products."
            )

    # Execute the query using the determined ID
    # Note: Using .filter() is generally safer than .get() for collection queries
    return (
        db.query(SupplierProduct)
        .filter(SupplierProduct.supplier_id == actual_supplier_id)
        .all()
    )

@router.get("/stats")
def supplier_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required([RoleEnum.SUPPLIER, RoleEnum.ADMIN]))
):
    total_suppliers = db.query(Supplier).count()
    suppliers_by_city = (
        db.query(Supplier.city, func.count(Supplier.supplier_id))
        .group_by(Supplier.city)
        .all()
    )
    return {
        "total_suppliers": total_suppliers,
        "suppliers_by_city": {city: count for city, count in suppliers_by_city}
    }

# 6. List Supplier Products
@router.get("/get_all_supplier/{supplier_id}", response_model=List[SupplierProductResponse])
def list_supplier_products(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required(RoleEnum.SUPPLIER, RoleEnum.CHEMIST))
):
    try:
        supplier_products = db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == supplier_id
        ).all()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}"
        )

    if not supplier_products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No supplier products found."
        )

    response = []
    for sp in supplier_products:
        try:
            # Pydantic now handles Base64 conversion automatically via validator
            product_data = ProductNested.from_orm(sp.product)
            # still assign mime type if present
            product_data.image_mime = sp.product.image_mime if sp.product.image else None

            supplier_data = SupplierNested.from_orm(sp.supplier)

            response.append(
                SupplierProductResponse(
                    supplier_product_id=sp.supplier_product_id,
                    supplier_id=sp.supplier_id,
                    product_id=sp.product_id,
                    created_at=sp.created_at,
                    supplier_sku=sp.supplier_sku,
                    lead_time_days=sp.lead_time_days,
                    price=sp.price,
                    product=product_data,
                    supplier=supplier_data,
                )
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize supplier product data: {str(exc)}"
            )
    
    return response

    
# Get All Products (Paginated + Searchable)
@router.get("/products/search", response_model=Page[ProductResponse])
def get_all_products(
    name: Optional[str] = Query(None, description="Filter by product name"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(role_required([RoleEnum.CHEMIST, RoleEnum.SUPPLIER]))
):
    """
    Get all products in the system (global list).
    Supports pagination and filtering by name, brand, and category.
    """
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    products = query.all()
    return paginate(products)

# ========= CUSTOMER ROUTES =========

# -------------------------
# Create Customer (linked to User)
# -------------------------
@router.post("/customers", response_model=CustomerResponse)
def create_customer_route(
    customer: CustomerCreate,  # incoming request with email
    db: Session = Depends(get_db),
    user_chemist: User = Depends(role_required([RoleEnum.CHEMIST]))
):
    try:
        # 1️⃣ Find the existing User by email
        existing_user = db.query(User).filter(User.email == customer.email).first()
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="Customer email is not registered as an application user. Please register the user first."
            )

        customer_app_id: UUID = existing_user.id  # Use the User's UUID

        # 2️⃣ Find the store associated with the chemist
        store = db.query(MedicalStore).filter(MedicalStore.owner_id == user_chemist.id).first()
        if not store:
            raise HTTPException(
                status_code=404,
                detail="No store found for this chemist"
            )

        # 3️⃣ Check if this User is already a customer at this store
        existing_customer_profile = db.query(Customer).filter(
            Customer.customer_id == customer_app_id,
            Customer.store_id == store.store_id
        ).first()
        if existing_customer_profile:
            raise HTTPException(
                status_code=400,
                detail="This application user is already registered as a customer at this store."
            )

        # 4️⃣ Create Customer profile (use existing User ID)
        new_customer = Customer(
            customer_id=str(customer_app_id),
            store_id=str(store.store_id),
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            age=customer.age,
            gender=customer.gender,
            address=customer.address,
            role=customer.role or "CUSTOMER",
            latitude=customer.latitude,
            longitude=customer.longitude
        )

        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        return new_customer

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while creating customer: {str(e)}"
        )

# Get Customers
@router.get("/customers/find/", response_model=Page[CustomerResponse])
def find_customers(
    name: str = None,
    phone: str = None,
    email: str = None,
    address: str = None,
    db: Session = Depends(get_db),
    user: dict = Depends(role_required([RoleEnum.CHEMIST]))
):
    try:
        store = db.query(MedicalStore).filter(MedicalStore.owner_id == user.id).first()
        if not store:
            raise HTTPException(404, detail="No store found for this chemist")
        query = db.query(Customer).filter(Customer.store_id == store.store_id)
        if name:
            query = query.filter(Customer.name.ilike(f"%{name}%"))
        if phone:
            query = query.filter(Customer.phone.like(f"%{phone}%"))
        if email:
            query = query.filter(Customer.email.ilike(f"%{email}%"))
        if address:
            query = query.filter(Customer.address.ilike(f"%{address}%"))
        customers = query.all()
        if not customers:
            raise HTTPException(404, detail="No customers found with the given criteria")
        return paginate(customers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Internal server error while fetching customers: {str(e)}")

# Update Customer by Name (Case-Insensitive)
@router.put("/customers/update/{name:path}", response_model=CustomerResponse)
def update_customer(
    name: str,
    updated_customer: CustomerUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(role_required(RoleEnum.CHEMIST)),
):
    try:
        store = db.query(MedicalStore).filter(MedicalStore.owner_id == user.id).first()
        if not store:
            raise HTTPException(status_code=404, detail="No store found for this chemist")
        customer = (
            db.query(Customer)
            .filter(Customer.store_id == store.store_id)
            .filter(func.lower(Customer.name) == name.lower())
            .first()
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if updated_customer.email:
            existing_customer = (
                db.query(Customer)
                .filter(Customer.email == updated_customer.email)
                .filter(Customer.customer_id != customer.customer_id)
                .first()
            )
            if existing_customer:
                raise HTTPException(
                    status_code=400,
                    detail=f"Email '{updated_customer.email}' already exists for another customer."
                )
        update_data = updated_customer.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer, key, value)
        db.commit()
        db.refresh(customer)
        return customer
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while updating customer: {str(e)}"
        )

# Delete Customer 
@router.delete("/customers/delete/")
def delete_customer_by_field(
    name: str = None,
    phone: str = None,
    email: str = None,
    address: str = None,
    db: Session = Depends(get_db),
    user: dict = Depends(role_required(RoleEnum.CHEMIST)),
):
    query = db.query(Customer)
    if name:
        query = query.filter(Customer.name == name)
    if phone:
        query = query.filter(Customer.phone == phone)
    if email:
        query = query.filter(Customer.email == email)
    if address:
        query = query.filter(Customer.address == address)
    db_customer = query.first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(db_customer)
    db.commit()
    return {"detail": "Customer deleted"}

# ========= PRESCRIPTION ROUTES =========

# -----------------------------
# Create Prescription (Role-Based ID Assignment)
# -----------------------------
@router.post(
    "/prescription", 
     response_model=PrescriptionResp, # Use your Pydantic response model
    status_code=status.HTTP_201_CREATED, 
    dependencies=[Depends(role_required("patient", "customer"))]
)
def create_prescription(
    # Client ONLY needs to send non-ID fields and the file.
    # We keep store_id as optional input for advanced use cases, but it should be omitted by default.
    
    doctor_name: str = Form(None, description="Name of the prescribing doctor"),
    notes: str = Form(None, description="Notes for the chemist"),
    
    file: UploadFile = File(..., description="The prescription document image/PDF"),
    
    # Dependencies
    current_user = Depends(get_current_user), # Authenticated user data (must have .id and .role)
    db: Session = Depends(get_db)
):
    # 1. Initialize all IDs to None
    final_customer_id = None
    final_patient_id = None
    final_store_id = None # Use override if provided
    
    # Ensure current user's ID is a Python UUID object for assignment
    auth_user_uuid = str(current_user.id)
    
    # 2. Role-Based ID Assignment Logic
    if current_user.role == "customer":
        # The authenticated user's ID becomes the customer_id
        final_customer_id = auth_user_uuid
        # patient_id remains None (as per requirement)

    elif current_user.role == "patient":
        # The authenticated user's ID becomes the patient_id
        final_patient_id = auth_user_uuid
        # customer_id remains None (as per requirement)
        
        # NOTE on store_id for Patient: 
        # If store_id is NOT NULL in the DB, you MUST fetch it here
        # by looking up the Patient's profile based on final_patient_id.
        # Since the model shows nullable=True, we proceed without lookup.


    # 3. Final Validation
    if not final_customer_id and not final_patient_id:
        # This should theoretically not happen due to role_required, but is a safe check
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Could not determine a valid Customer or Patient ID from your token."
        )

    # 4. Handle File Content
    try:
        content = file.file.read() 
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not read the uploaded file.")

    # 5. Create the Prescription Object
    pres = Prescription(
        prescription_id=str(uuid.uuid4()),
        
        # Assigning UUID objects or None to prevent SQL conversion errors
        customer_id=final_customer_id,  
        patient_id=final_patient_id,    
        store_id=final_store_id,        
        
        doctor_name=doctor_name,
        notes=notes,
        file_content=content,
        file_mime=file.content_type,
    )

    # 6. Database Commit
    try:
        db.add(pres)
        db.commit()
        db.refresh(pres)
        return pres
    except Exception as e:
        db.rollback()
        # Ensure rollback in case of error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create prescription: {e}"
        )
        
# -----------------------------
# Get Prescription by ID
# -----------------------------
@router.get("/get_prescription/{prescription_id}", response_model=PrescriptionResp, dependencies=[Depends(role_required("patient","chemist"))])
def get_prescription(prescription_id: str, db: Session = Depends(get_db)):
    pres = db.query(Prescription).filter_by(prescription_id=prescription_id).first()
    if not pres:
        raise HTTPException(404, "Prescription not found")
    return pres


# -----------------------------
# List by Patient
# -----------------------------
@router.get("/patient/{patient_id}", response_model=List[PrescriptionResp], dependencies=[Depends(role_required("patient","chemist","pharmacist"))])
def list_patient_prescriptions(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Prescription).filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()


# -----------------------------
# Delete Prescription
# -----------------------------
@router.delete("/prescription_delete/{prescription_id}", status_code=204, dependencies=[Depends(role_required("patient","chemist"))])
def delete_prescription(prescription_id: str, db: Session = Depends(get_db)):
    pres = db.query(Prescription).filter_by(prescription_id=prescription_id).first()
    if not pres:
        raise HTTPException(404, "Prescription not found")
    db.delete(pres)
    db.commit()
    return
# -----------------------------
# Get All Responses for Customer/Patient Prescriptions
# -----------------------------
@router.get("/all_chemist/my_responses", response_model=List[PrescriptionResponseRead])
def get_all_responses_for_my_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("patient", "customer"))
):
    user_id_str = str(current_user.id)
    
    # 1. Find all prescriptions owned by this user (either as customer or patient)
    my_prescriptions = db.query(Prescription).filter(
        or_(Prescription.customer_id == user_id_str, Prescription.patient_id == user_id_str)
    ).all()
    
    if not my_prescriptions:
        return []

    prescription_ids = [p.prescription_id for p in my_prescriptions]

    # 2. Fetch all responses linked to those prescription IDs
    all_responses = db.query(PrescriptionResponse).filter(
        PrescriptionResponse.prescription_id.in_(prescription_ids)
    ).order_by(PrescriptionResponse.responded_at.desc()).all()
    
    return all_responses

# -----------------------------
# Get All Open Prescriptions (Chemist Bidding Feed)
# -----------------------------
@router.get("/chemist/open_prescriptions", response_model=List[PrescriptionResp])
def get_open_prescriptions_for_bidding(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("chemist", "store_owner"))
):
    # A prescription is "open" if store_id is NULL (unassigned)
    open_prescriptions = db.query(Prescription).filter(
        Prescription.store_id == None
    ).order_by(Prescription.created_at.desc()).all()
    
    return open_prescriptions

# -----------------------------
# Create Response (Store Role)
# -----------------------------
@router.post("/response", response_model=PrescriptionResponseRead)
def create_prescription_response(
    response_in: PrescriptionResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["store_owner", "store_admin", "chemist"]:
        raise HTTPException(status_code=403, detail="Only store owners or chemists can respond.")

    store = db.query(MedicalStore).filter(MedicalStore.owner_id == current_user.id).first()
    if not store:
        raise HTTPException(404, "No store found for this chemist")

    prescription = db.query(Prescription).filter(
        Prescription.prescription_id == response_in.prescription_id
    ).first()
    if not prescription:
        raise HTTPException(404, "Prescription not found")

    new_response = PrescriptionResponse(
        prescription_id=response_in.prescription_id,
        store_id=store.store_id,
        status=response_in.status,
        available_items_json=response_in.available_items_json,
        message=response_in.message,
        responded_at=datetime.utcnow(),
    )

    try:
        db.add(new_response)
        db.commit()
        db.refresh(new_response)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return new_response


# -----------------------------
# Get All Responses (Admin/Chemist)
# -----------------------------
@router.get("/store/{store_id}", response_model=List[PrescriptionResponseRead])
def get_responses_by_store(store_id: UUID, db: Session = Depends(get_db)):
    return db.query(PrescriptionResponse).filter(PrescriptionResponse.store_id == store_id).all()


# -----------------------------
# Get Responses by Prescription
# -----------------------------
@router.get("/responses/by-prescription/{prescription_id}", response_model=List[PrescriptionResponseRead])
def get_responses_by_prescription(
    prescription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(RoleEnum.CHEMIST))
):
    responses = db.query(PrescriptionResponse).filter(
        PrescriptionResponse.prescription_id == prescription_id
    ).all()
    if not responses:
        raise HTTPException(404, "No responses found")
    return responses

# -----------------------------
# 💊 Get Prescription Document (Secured via Query Token)
# -----------------------------
@router.get("/prescription/{prescription_id}/document")
def get_prescription_document(
    prescription_id: UUID,
    token: str = Query(..., description="JWT token for authorization"),
    db: Session = Depends(get_db)
):
    """
    ✅ Securely return a prescription PDF directly from the MSSQL database
    using JWT token passed in the query parameter.
    """

    # 1️⃣ AUTHENTICATE TOKEN
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(HTTP_401_UNAUTHORIZED, detail="Invalid token: user_id missing.")
        
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(HTTP_404_NOT_FOUND, detail="User not found.")
        
        allowed_roles = {"chemist", "store_owner", "patient"}
        if current_user.role.lower() not in allowed_roles:
            raise HTTPException(HTTP_403_FORBIDDEN, detail="Unauthorized role to view document.")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired token: {str(e)}")

    # 2️⃣ FETCH FILE FROM DATABASE
    prescription = (
        db.query(Prescription)
        .filter(Prescription.prescription_id == str(prescription_id))
        .first()
    )

    if not prescription:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Prescription not found in database.")
    
    if not prescription.file_content:
        raise HTTPException(HTTP_404_NOT_FOUND, detail="Prescription binary content missing.")
    
    mime_type = prescription.file_mime or "application/pdf"
    
    # 3️⃣ STREAM RESPONSE
    file_stream = BytesIO(prescription.file_content)
    file_stream.seek(0)
    
    return StreamingResponse(
        file_stream,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="Prescription_{prescription_id}.pdf"'
        },
    )

# -----------------------------
# Update Response
# -----------------------------
@router.put("/response/{response_id}", response_model=PrescriptionResponseRead)
def update_response(
    response_id: str,
    update_in: PrescriptionResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required(RoleEnum.CHEMIST))
):
    response = db.query(PrescriptionResponse).filter_by(response_id=response_id).first()
    if not response:
        raise HTTPException(404, "Response not found")

    store = db.query(MedicalStore).filter(MedicalStore.owner_id == current_user.id).first()
    if not store or response.store_id != store.store_id:
        raise HTTPException(403, "Not authorized to update this response")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(response, field, value)

    db.commit()
    db.refresh(response)
    return response


# -----------------------------
# Delete Response
# -----------------------------
@router.delete("/response/{response_id}", status_code=204)
def delete_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["chemist", "store_owner"]:
        raise HTTPException(403, "Unauthorized access")

    response = db.query(PrescriptionResponse).filter_by(response_id=response_id).first()
    if not response:
        raise HTTPException(404, "Response not found")

    db.delete(response)
    db.commit()


# -----------------------------
# Assign Store to Prescription (Patient)
# -----------------------------
@router.post("/assign-store", response_model=PrescriptionResp)
def assign_store_to_prescription(
    prescription_id: str,
    store_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ Ensure only patients can assign a store
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can assign a store.")

    # ✅ Fetch the patient linked to the user
    patient = db.query(Patient).filter(Patient.name == current_user.username).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # ✅ Fetch the prescription
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # ✅ Ownership check (compare patient_id, not user.id)
    if prescription.patient_id != patient.patient_id:
        raise HTTPException(status_code=403, detail="You are not the owner of this prescription.")

    # ✅ Ensure store actually responded
    store_response = db.query(PrescriptionResponse).filter(
        PrescriptionResponse.prescription_id == prescription_id,
        PrescriptionResponse.store_id == store_id
    ).first()
    if not store_response:
        raise HTTPException(status_code=400, detail="Selected store has not responded to this prescription.")

    # ✅ Update store_id
    prescription.store_id = store_id
    db.commit()
    db.refresh(prescription)

    return prescription

@router.get("/{prescription_id}/assigned-store", response_model=dict)
def get_assigned_store(
    prescription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    
    # ✅ Permission check
    if current_user.role not in ["patient", "doctor", "chemist"]:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    if not prescription.store_id:
        return {"message": "No store assigned yet."}

    store = db.query(MedicalStore).filter(MedicalStore.store_id == prescription.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Assigned store not found.")

    return {
        "store_id": store.store_id,
        "store_name": store.store_name,
        "owner_id": store.owner_id
    }

# -----------------------------
# Get Assigned Prescriptions (Chemist/Store)
# -----------------------------
@router.get("/prescriptions/assigned", response_model=List[PrescriptionResp])
def get_store_assigned_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches all prescriptions that have been specifically assigned to the 
    current user's registered medical store by a patient.
    
    Access is restricted to 'chemist', 'store_owner', and 'patient' roles.
    """
    if current_user.role not in ["chemist", "store_owner", "patient"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Unauthorized access. Only chemists, store owners, or patients can view assigned prescriptions."
        )
    
    # 1. Find the store owned by this chemist using the current user's ID
    store = db.query(MedicalStore).filter(MedicalStore.owner_id == current_user.id).first()
    
    if not store:
        # Note: If the user is a 'patient' or a 'store_owner' without a store 
        # (which shouldn't happen for 'store_owner'), this is the correct response.
        # If the user is a patient, you might redirect them or change this logic.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Store profile not found for the current user."
        )
    
    # 2. Query prescriptions where the 'store_id' field matches the found store's ID
    prescriptions = db.query(Prescription).filter(Prescription.store_id == store.store_id).all()
    
    # 3. Return the list of assigned prescriptions
    return prescriptions

# ========= BILL & BILLITEM ROUTES =========

# ------------------------------
# 1. ✅ CREATE BILL ENDPOINT (FINAL VERSION)
# ------------------------------
@router.post("/bill", response_model=BillResp, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    def clean_id(value: Optional[str]) -> Optional[str]:
        if not value or value.strip().lower() in ["string", "null", "none", ""]:
            return None
        return value.strip()

    customer_id = clean_id(bill_data.customer_id)
    patient_id = clean_id(bill_data.patient_id)
    product_id = clean_id(bill_data.product_id)
    authorized_store_id = None
    authorized_supplier_id = None

    if current_user.role in ["chemist", "supplier"]:
        store = db.query(MedicalStore).filter_by(owner_id=current_user.id).first()
        if not store:
            raise HTTPException(404, "Store not found for this user.")
        authorized_store_id = str(store.store_id)

        payload_store_id = clean_id(bill_data.issuer_store_id)
        if payload_store_id and payload_store_id.lower() != authorized_store_id.lower():
            raise HTTPException(403, "Unauthorized issuer_store_id provided in payload.")

    elif current_user.role == "supplier":
        supplier = db.query(Supplier).filter_by(user_id=current_user.id).first()
        if not supplier:
            raise HTTPException(404, "Supplier not found for this user.")
        authorized_supplier_id = str(supplier.supplier_id)

        payload_supplier_id = clean_id(bill_data.issuer_supplier_id)
        if payload_supplier_id and payload_supplier_id.lower() != authorized_supplier_id.lower():
            raise HTTPException(403, "Unauthorized issuer_supplier_id provided in payload.")
    else:
        raise HTTPException(403, "Unauthorized role to create a bill.")

    # XOR check: exactly one recipient required
    if sum(bool(r) for r in [customer_id, patient_id]) != 1:
        raise HTTPException(400, "Bill must target exactly one recipient.")

    # Validate UUIDs
    uuid_re = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    for id_value in [customer_id, patient_id, product_id, authorized_store_id, authorized_supplier_id]:
        if id_value and not re.match(uuid_re, id_value, re.IGNORECASE):
            raise HTTPException(400, f"Invalid UUID: {id_value}")

    # Create Bill
    new_bill = Bill(
        bill_id=str(uuid.uuid4()),
        issuer_store_id=authorized_store_id,
        issuer_supplier_id=authorized_supplier_id,
        customer_id=customer_id,
        patient_id=patient_id,
        product_id=product_id,
        subtotal=bill_data.subtotal,
        tax_amount=bill_data.tax_amount,
        total_amount=bill_data.total_amount,
    )
    db.add(new_bill)
    db.flush()

    # Add bill items and manage stock
    item_responses: List[BillItemResp] = []
    for item in bill_data.items:
        product = db.query(Product).filter_by(product_id=item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(404, f"Product {item.product_id} not found.")

        if authorized_store_id:
            inventory = db.query(Inventory).filter(
                Inventory.product_id == item.product_id, Inventory.batch_no == item.batch_no
            ).first()
            if not inventory:
                db.rollback()
                raise HTTPException(404, f"Stock record not found for product {item.product_id} batch {item.batch_no}.")
            
            if inventory.quantity < item.quantity:
                db.rollback()
                raise HTTPException(400, f"Insufficient stock for {product.name} batch {item.batch_no}.")
            
            inventory.quantity -= item.quantity

        new_item = BillItem(
            bill_item_id=str(uuid.uuid4()),
            bill_id=new_bill.bill_id,
            **item.model_dump()
        )
        db.add(new_item)
        item_responses.append(BillItemResp.model_validate(new_item))

    db.commit()
    db.refresh(new_bill)

    return BillResp(**new_bill.__dict__, items=item_responses)

# -----------------------------------------------------
# 2. 🔹 GET BILL BY ID
# -----------------------------------------------------
@router.get("/bill/{bill_id}", response_model=BillResp)
def get_bill(bill_id: str, db: Session = Depends(get_db)):
    # Note: Authorization (checking if the user is the issuer/recipient) should be added here
    bill = db.query(Bill).filter_by(bill_id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # The Bill model's 'items' relationship loads the BillItems automatically
    return BillResp.model_validate(bill)

# -----------------------------------------------------
# 3. 🔹 LIST BILLS FOR CURRENT ISSUER (READ)
# -----------------------------------------------------
@router.get("/my_bills", response_model=List[BillResp])
def list_my_bills(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Bill)

    if current_user.role in ["store_admin", "chemist"]:
        store = db.query(MedicalStore).filter_by(owner_id=current_user.id).first()
        if not store:
            raise HTTPException(404, "Store not found")
        query = query.filter(Bill.issuer_store_id == store.store_id)
    elif current_user.role == "supplier":
        supplier = db.query(Supplier).filter_by(user_id=current_user.id).first()
        if not supplier:
            raise HTTPException(404, "Supplier not found")
        query = query.filter(Bill.issuer_supplier_id == supplier.supplier_id)
    else:
        raise HTTPException(403, "Unauthorized role to view bills.")

    bills = query.order_by(Bill.created_at.desc()).all()
    return [BillResp.model_validate(bill) for bill in bills]

# -----------------------------------------------------
# 4. 🗑️ DELETE BILL (DELETE)
# -----------------------------------------------------
@router.delete("/bill/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    bill = db.query(Bill).filter_by(bill_id=bill_id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")

    is_store_issuer = bill.issuer_store_id and current_user.role in ["chemist", "supplier"]
    is_supplier_issuer = bill.issuer_supplier_id and current_user.role == "supplier"

    if is_store_issuer:
        store = db.query(MedicalStore).filter_by(owner_id=current_user.id).first()
        if not store or str(store.store_id) != str(bill.issuer_store_id):
            raise HTTPException(403, "Not authorized to delete this store bill.")
    elif is_supplier_issuer:
        supplier = db.query(Supplier).filter_by(user_id=current_user.id).first()
        if not supplier or str(supplier.supplier_id) != str(bill.issuer_supplier_id):
            raise HTTPException(403, "Not authorized to delete this supplier bill.")
    else:
        raise HTTPException(403, "Not authorized to delete this bill.")

    db.delete(bill)
    db.commit()
    return

# ========= ORDERS ROUTES =========

# -----------------------------------------------------
# 1. 🟢 CREATE ORDER (POST)
# -----------------------------------------------------
@router.post("/order", response_model=OrderResp, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["chemist"]))
):
    store = db.query(MedicalStore).filter(
        MedicalStore.owner_id == str(current_user.id),
        MedicalStore.store_id == payload.store_id
    ).first()
    if not store:
        raise HTTPException(403, "Store not found or unauthorized")

    supplier = db.query(Supplier).filter(Supplier.supplier_id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    if not payload.items or len(payload.items) == 0:
        raise HTTPException(400, "Order must contain at least one item")

    order_items = []
    total_amount = 0.0

    for item_payload in payload.items:
        supplier_product = db.query(SupplierProduct).filter(
            SupplierProduct.supplier_id == payload.supplier_id,
            SupplierProduct.product_id == item_payload.product_id
        ).first()

        unit_price = None
        if supplier_product:
            unit_price = float(supplier_product.price)
        else:
            product_check = db.query(Product).filter(Product.product_id == item_payload.product_id).first()
            if not product_check:
                raise HTTPException(404, f"Product ID {item_payload.product_id} not found.")
            if item_payload.price is None:
                raise HTTPException(400, f"Unmapped product {item_payload.product_id} requires price.")
            unit_price = float(item_payload.price)

        if unit_price is None or item_payload.quantity <= 0:
            raise HTTPException(400, f"Invalid price or quantity for product {item_payload.product_id}.")

        line_total = round(unit_price * item_payload.quantity, 2)
        total_amount += line_total

        order_item = OrderItem(
            order_item_id=str(uuid.uuid4()),
            product_id=item_payload.product_id,
            supplier_id=payload.supplier_id,
            quantity=item_payload.quantity,
            price=unit_price,
        )
        order_items.append(order_item)

    new_order = Order(
        order_id=str(uuid.uuid4()),
        store_id=payload.store_id,
        supplier_id=payload.supplier_id,
        order_date=payload.order_date if payload.order_date else datetime.utcnow(),
        status=payload.status,
        total_amount=total_amount,
        items=order_items
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

# -----------------------------------------------------
# 2. 🟢 GET SINGLE ORDER (READ)
# -----------------------------------------------------
@router.get("/order/{order_id}", response_model=OrderResp, 
            dependencies=[Depends(role_required(["chemist", "supplier"]))])
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    """Retrieves a single order by ID, eagerly loading its items."""
    
    # Eagerly load the 'items' relationship
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter_by(order_id=order_id)
        .first()
    )
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    return order

# -----------------------------------------------------
# 3. 🟢 LIST STORE ORDERS (READ)
# -----------------------------------------------------
@router.get("/order/store/{store_id}", response_model=List[OrderResp], 
            dependencies=[Depends(role_required(["chemist", "supplier"]))])
def list_store_orders(store_id: UUID, db: Session = Depends(get_db)):
    """Lists all orders placed by a specific store, eagerly loading items."""
    
    # Eagerly load the items to prevent the N+1 problem
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter_by(store_id=store_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# -----------------------------------------------------
# 4. 🟢 LIST SUPPLIER ORDERS (READ) - Added for completeness
# -----------------------------------------------------
@router.get("/order/supplier/{supplier_id}", response_model=List[OrderResp], 
            dependencies=[Depends(role_required(["supplier", "chemist"]))])
def list_supplier_orders(supplier_id: UUID, db: Session = Depends(get_db)):
    """Lists all orders received by a specific supplier, eagerly loading items."""
    
    # Eagerly load the items to prevent the N+1 problem
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter_by(supplier_id=supplier_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# -----------------------------------------------------
# 5. 🟢 UPDATE ORDER STATUS (PATCH)
# -----------------------------------------------------
# Use a dedicated Pydantic model for status updates for clean validation
class OrderStatusUpdate(BaseModel):
    status: str
    
    # Optional: Define allowed status values here
    # @field_validator('status')
    # def validate_status(cls, value):
    #     if value not in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
    #         raise ValueError('Invalid status')
    #     return value

@router.patch("/order/{order_id}/status", response_model=OrderResp, 
              dependencies=[Depends(role_required(["chemist", "supplier"]))])
def update_order_status(order_id: UUID, status_payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    """Updates the status of a specific order."""
    
    order = db.query(Order).filter_by(order_id=order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    order.status = status_payload.status
    db.commit()
    
    # Refresh and Eager Load for response
    db.refresh(order, attribute_names=['items'])
    
    return order

# -----------------------------------------------------
# 6. 🔴 DELETE ORDER (DELETE)
# -----------------------------------------------------
@router.delete("/order/{order_id}", status_code=status.HTTP_204_NO_CONTENT, 
               dependencies=[Depends(role_required(["chemist", "supplier"]))])
def delete_order(order_id: UUID, db: Session = Depends(get_db)):
    """Deletes an order by ID. Cascade delete will remove associated OrderItems."""
    
    order = db.query(Order).filter_by(order_id=order_id).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
    db.delete(order)
    db.commit()
    
    return








# ========= STORE SETTINGS ROUTES =========

@router.get("/store_settigs/{store_id}", response_model=StoreSettingsResp, dependencies=[Depends(role_required("chemist"))])
def get_store_settings(store_id: str, db: Session = Depends(get_db)):
    s = db.query(StoreSettings).filter_by(store_id=store_id).first()
    if not s:
        raise HTTPException(404, "Settings not found")
    return s

@router.post("/store_settings", response_model=StoreSettingsResp, status_code=201, dependencies=[Depends(role_required("chemist"))])
def create_store_settings(payload: StoreSettingsCreate, db: Session = Depends(get_db)):
    s = StoreSettings(
        store_settings_id=str(uuid.uuid4()),
        store_id=payload.store_id,
        accepts_online_orders=payload.accepts_online_orders,
        notif_on_low_stock=payload.notif_on_low_stock,
        low_stock_threshold=payload.low_stock_threshold
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.put("/store_settings/{store_settings_id}", response_model=StoreSettingsResp, dependencies=[Depends(role_required("chemist"))])
def update_store_settings(store_settings_id: str, payload: StoreSettingsCreate, db: Session = Depends(get_db)):
    s = db.query(StoreSettings).filter_by(store_settings_id=store_settings_id).first()
    if not s:
        raise HTTPException(404, "Settings not found")
    s.accepts_online_orders = payload.accepts_online_orders
    s.notif_on_low_stock = payload.notif_on_low_stock
    s.low_stock_threshold = payload.low_stock_threshold
    db.commit()
    db.refresh(s)
    return s

# ========= AUDIT LOG ROUTES =========

@router.post("/audit_log", response_model=AuditLogResp, status_code=201, dependencies=[Depends(role_required("chemist"))])
def create_audit(payload: AuditLogCreate, db: Session = Depends(get_db)):
    a = AuditLog(
        log_id=str(uuid.uuid4()),
        store_id=payload.store_id,
        user_id=payload.user_id,
        action=payload.action,
        details=payload.details
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@router.get("/store/audit_log/{store_id}", response_model=List[AuditLogResp], dependencies=[Depends(role_required("chemist"))])
def list_store_logs(store_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter_by(store_id=store_id).order_by(AuditLog.timestamp.desc()).all()
    return logs

# ========= DASHBOARD ROUTES =========

@router.get(
    "/store/dashbord/{store_id}", 
    response_model=MedicalStoreDashboardResp, 
    status_code=status.HTTP_200_OK
)
def get_dashboard(
    # 1. Non-default argument (from path)
    store_id: uuid.UUID, 
    
    # 2. Dependency without an inline default (assuming CurrentUser is defined using Annotated[..., Depends(...)])
    current_user: CurrentUser, 
    
    # 3. Dependency with an inline default MUST come last
    db: Session = Depends(get_db)
):
    """
    Retrieves the dashboard data for a specific store, verifying user ownership.
    """
    
    # 1. Authorization: Verify the current user owns the store_id
    store = db.query(MedicalStore).filter(
        MedicalStore.store_id == store_id,
        MedicalStore.owner_id == str(current_user.id)
    ).first()

    if not store:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied: Store not found or you are not the authorized owner."
        )

    # 2. Data Retrieval: Fetch the dashboard view data
    vw = db.query(MedicalStoreDashboard).filter_by(store_id=store_id).first()
    
    # 3. Handle 404 
    if not vw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Dashboard data not yet available for store ID: {store_id}"
        )
        
    # 4. Return the data
    return vw