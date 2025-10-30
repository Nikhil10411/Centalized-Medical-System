from datetime import datetime, date, time
from sqlalchemy import ( UniqueConstraint,Column, LargeBinary, 
                         String, Integer, DateTime, ForeignKey, 
                         Boolean, Text, Float, Time, Date, Enum as SqlEnum,
                         CheckConstraint, DECIMAL, Computed, Table, Enum
)

from database import engine
from sqlalchemy.sql import func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid

def generate_uuid():
    return str(uuid.uuid4())

Base = declarative_base()

vw_MedicalStoreDashboard = Table(
    "vw_MedicalStoreDashboard",
    Base.metadata,
    autoload_with=engine
)
# -----------------------------
# ENUM for Subscription Status
# -----------------------------
class SubscriptionStatus(str, enum.Enum):
    created = "created"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


class RoleEnum(str, enum.Enum):
    ADMIN   = "admin"
    DOCTOR  = "doctor"
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



# ──────────────────────────────
# 1. User
# ──────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SqlEnum(RoleEnum, native_enum=False), default=RoleEnum.PATIENT)
    is_admin = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    created_suppliers = relationship("Supplier", back_populates="creator") 
    customer = relationship("Customer", back_populates="user", uselist=False)
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    subscriptions = relationship("Subscription", back_populates="user")

    #hospital = relationship("Hospital", back_populates="users")
   # patient = relationship("Patient", back_populates="user", uselist=False)


# -------------------------
# 1. Patient
# -------------------------
class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # ✅ New fields from ALTER TABLE
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)   # Example: "Male", "Female", "Other"
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    pin_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # ✅ Relationships
    medical_histories = relationship("MedicalHistory", back_populates="patient", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="patient", cascade="all, delete-orphan")


# -------------------------
# 2. Doctor
# -------------------------
class Doctor(Base):
    __tablename__ = "doctors"

    # --- 1. CORE & PRIMARY KEY (Linked to User Table) ---
    # The doctor_id is a Foreign Key referencing the 'users' table.
    doctor_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    
    # --- 2. ORIGINAL FIELDS RETAINED ---
    name = Column(String(200), nullable=False)
    specialization = Column(String(200), index=True)
    age = Column(Integer, nullable=True)             # RETAINED
    gender = Column(String(20), nullable=True)       # RETAINED
    
    # --- 3. LOGICAL PROFESSIONAL FIELDS ---
    medical_license_number = Column(String(100), unique=True, nullable=False)
    regulatory_body = Column(String(100))
    
    # Contact/Experience
    contact_phone = Column(String(20))
    experience_years = Column(Integer, default=0)
    education_degree = Column(String(100))
    is_available = Column(Boolean, default=True)

    # --- 4. CLINIC & LOCATION FIELDS ---
    clinic_name = Column(String(255))
    clinic_address = Column(String(255), nullable=False) 

    # Location for Geo-search
    latitude = Column(Float)
    longitude = Column(Float)
    
    # --- 5. MEDIA FIELDS (Stored as BLOBs/VARBINARY(MAX)) ---
    doctor_photo = Column(LargeBinary, nullable=True) 
    license_photo = Column(LargeBinary, nullable=False) # Mandatory
    clinic_photo = Column(LargeBinary, nullable=True)

    # --- 6. TIMESTAMPS ---
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # --- 7. RELATIONSHIPS ---
    # Relationship back to the User model
    user = relationship("User", back_populates="doctor_profile")
    
    # Relationship to MedicalHistory (kept from your original model)
    medical_histories = relationship("MedicalHistory", back_populates="doctor")

# -------------------------
# 3. Patient Medical History
# -------------------------
class MedicalHistory(Base):
    __tablename__ = "patient_medical_history"

    history_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.doctor_id"), nullable=False)

    diagnosis = Column(Text)
    test_results = Column(Text)
    medicines = Column(Text)
    surgery_notes = Column(Text)
    visit_date = Column(DateTime, default=datetime.utcnow)
    document_file = Column(LargeBinary,nullable=True)
    document_mime_type = Column(String(100), nullable=True) 
    image_mime_type = Column(String(100), nullable=True)       
    image_file = Column(LargeBinary,nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    latitude = Column(Float, nullable=True)                 # float
    longitude = Column(Float, nullable=True)                # float

    # ✅ Relationships
    patient = relationship("Patient", back_populates="medical_histories")
    doctor = relationship("Doctor", back_populates="medical_histories")

# -------------------------
# Inventory
# -------------------------
class Inventory(Base):
    __tablename__ = "Inventory"

    inventory_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("Product.product_id", ondelete="CASCADE"), nullable=False)

    product_name = Column(String(255), nullable=False)   # nvarchar
    batch_no = Column(String(100), nullable=True)        # nvarchar
    expiry_date = Column(DateTime, nullable=True)        # datetime2

    quantity = Column(Integer, nullable=False, default=0)   # int
    price = Column(DECIMAL(18, 2), nullable=False, default=0)  # decimal

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    store = relationship("MedicalStore", back_populates="inventories")
    product = relationship("Product", back_populates="inventories")

# -------------------------
# Medical Store
# -------------------------
class MedicalStore(Base):
    __tablename__ = "MedicalStore"

    store_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # uniqueidentifier
    store_name = Column(String(255), nullable=False)        # nvarchar
    owner_id = Column(String(36), nullable=False)           # uniqueidentifier
    owner_name = Column(String(255), nullable=False)        # nvarchar
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)   # Example: "Male", "Female", "Other"
    store_type = Column(String(255), nullable=True)         # nvarchar
    license_document = Column(LargeBinary, nullable=False)   # image
    license_mime = Column(String(255), nullable=True)       # nvarchar
    store_photo = Column(LargeBinary, nullable=False)        # image
    photo_mime = Column(String(255), nullable=True)         # nvarchar
    address = Column(Text, nullable=True)                   # nvarchar (long form)
    city = Column(String(255), nullable=True)               # nvarchar
    locality = Column(String(255), nullable=False)           # nvarchar
    pin_code = Column(String(20), nullable=False)            # nvarchar
    phone = Column(String(20), nullable=True)               # nvarchar
    email = Column(String(255), nullable=True)              # nvarchar
    open_hours = Column(String(255), nullable=True)         # nvarchar
    delivery_radius_km = Column(Integer, nullable=True)     # int
    latitude = Column(Float, nullable=True)                 # float
    longitude = Column(Float, nullable=True)                # float
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)            # datetime2

    suppliers = relationship("Supplier", back_populates="store", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="store", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="store", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="issuer_store", cascade="all, delete-orphan")
    settings = relationship("StoreSettings", back_populates="store", uselist=False, cascade="all, delete-orphan")
    dashboard = relationship("MedicalStoreDashboard", back_populates="store", uselist=False)
    inventories = relationship("Inventory", back_populates="store", cascade="all, delete-orphan")
    responses = relationship("PrescriptionResponse", back_populates="store")




# -------------------------
# Supplier
# -------------------------
class Supplier(Base):
    __tablename__ = "Supplier"

    supplier_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # uuid string
    supplier_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    pin_code = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=True)

    # New field to link the creator (chemist) user id
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    store = relationship("MedicalStore", back_populates="suppliers")
    products = relationship("SupplierProduct", back_populates="supplier", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="supplier")
    bills = relationship("Bill", back_populates="issuer_supplier", cascade="all, delete-orphan")

    # Optionally, you can add relationship to User model for 'created_by' if needed, eg:
    creator = relationship("User", back_populates="created_suppliers")

# -------------------------
# Product
# -------------------------
class Product(Base):
    __tablename__ = "Product"

    product_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # uniqueidentifier
    name = Column(String(255), nullable=False)             # nvarchar
    brand = Column(String(255), nullable=True)             # nvarchar
    generic_name = Column(String(255), nullable=True)      # nvarchar
    dosage = Column(String(255), nullable=True)            # nvarchar
    form = Column(String(255), nullable=True)              # nvarchar
    category = Column(String(255), nullable=True)          # nvarchar
    hsn_code = Column(String(255), nullable=True)          # nvarchar
    image = Column(LargeBinary, nullable=True)             # image
    image_mime = Column(String(255), nullable=True)        # nvarchar
    created_at = Column(DateTime(timezone=True), server_default=func.now())           # datetime2

    bill_items = relationship("BillItem", back_populates="product", cascade="all, delete-orphan")
    suppliers = relationship("SupplierProduct", back_populates="product", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    bills = relationship("Bill", back_populates="product")


# -------------------------
# Customer
# -------------------------
class Customer(Base):
    __tablename__ = "Customer"

    customer_id = Column(String(36),ForeignKey("users.id", ondelete="CASCADE"),primary_key=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)   # Example: "Male", "Female", "Other"
    address = Column(Text, nullable=True)
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)
    role = Column (String(40))
    latitude = Column(Float, nullable=True)                 # float
    longitude = Column(Float, nullable=True)                # float
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)


    store = relationship("MedicalStore", back_populates="customers")
    prescriptions = relationship("Prescription", back_populates="customer", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="customer", cascade="all, delete-orphan")
    user = relationship("User", back_populates="customer")


# -------------------------
# Prescription
# -------------------------
class Prescription(Base):
    __tablename__ = "Prescription"

    prescription_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("Customer.customer_id", ondelete="CASCADE"), nullable=True)
    patient_id = Column(String(36),ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=True)
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=True)
    doctor_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    file_content = Column(LargeBinary, nullable=True)             # image
    file_mime = Column(String(255), nullable=True)        # nvarchar
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="prescriptions")
    store = relationship("MedicalStore", back_populates="prescriptions")
    responses = relationship("PrescriptionResponse", back_populates="prescription", cascade="all, delete-orphan")
    patient = relationship("Patient", backref="prescriptions_as_patient", lazy="selectin")
    

class PrescriptionResponse(Base):
    __tablename__ = "PrescriptionResponse"

    response_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id = Column(String(36), ForeignKey("Prescription.prescription_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id"), nullable=True)
    status = Column(String(255), nullable=True)
    available_items_json = Column(String)
    message = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), server_default=func.now())

    prescription = relationship("Prescription", back_populates="responses")
    store = relationship("MedicalStore", back_populates="responses",lazy="selectin")
    #MedicalStore = relationship("MedicalStore", back_populates="responses", lazy="selectin" )


# -------------------------
# Bill + Items
# -------------------------
class Bill(Base):
    __tablename__ = "Bill"

    bill_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Issuer: store or supplier
    issuer_store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=True)
    issuer_supplier_id = Column(String(36), ForeignKey("Supplier.supplier_id", ondelete="CASCADE"), nullable=True)

    # Recipient: patient or customer
    customer_id = Column(String(36), ForeignKey("Customer.customer_id", ondelete="CASCADE"), nullable=True)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=True)

    # Optional single product reference
    product_id = Column(String(36), ForeignKey("Product.product_id", ondelete="CASCADE"), nullable=True)

    subtotal = Column(DECIMAL(18, 2), nullable=False, default=0)
    tax_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    total_amount = Column(DECIMAL(19, 2), nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    issuer_store = relationship("MedicalStore", back_populates="bills")
    issuer_supplier = relationship("Supplier", back_populates="bills")
    customer = relationship("Customer", back_populates="bills")
    patient = relationship("Patient", back_populates="bills")
    product = relationship("Product", back_populates="bills")

    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

    


class BillItem(Base):
    __tablename__ = "BillItem"

    bill_item_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = Column(String(36), ForeignKey("Bill.bill_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("Product.product_id", ondelete="NO ACTION"), nullable=False)

    batch_no = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    # Relationships
    bill = relationship("Bill", back_populates="items")
    product = relationship("Product", back_populates="bill_items")


# -------------------------
# Supplier Product Mapping
# -------------------------
class SupplierProduct(Base):
    __tablename__ = "SupplierProduct"

    supplier_product_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String(36), ForeignKey("Supplier.supplier_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("Product.product_id", ondelete="CASCADE"), nullable=False)
    
    # Match your DB columns exactly
    supplier_sku = Column(String(200), nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    price = Column(DECIMAL(18, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="products")
    product = relationship("Product", back_populates="suppliers")

    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
    )
# -------------------------
# Cart Model
# -------------------------
class Cart(Base):
    __tablename__ = "Cart"

    cart_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    store = relationship("MedicalStore")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


# -------------------------
# Cart Item Model
# -------------------------
class CartItem(Base):
    __tablename__ = "CartItem"

    cart_item_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id = Column(String(36), ForeignKey("Cart.cart_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("Product.product_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(DECIMAL(18, 2), nullable=False)
    subtotal = Column(DECIMAL(18, 2), Computed("quantity * price"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

# -------------------------
# Orders Model
# -------------------------
class Order(Base):
    __tablename__ = "Orders"

    order_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    store_id = Column(UNIQUEIDENTIFIER, ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UNIQUEIDENTIFIER, ForeignKey("Supplier.supplier_id", ondelete="CASCADE"), nullable=False)

    order_date = Column(DateTime, server_default=func.sysutcdatetime())
    status = Column(String(50), nullable=False, default="pending")  # pending, confirmed, shipped, etc.
    total_amount = Column(DECIMAL(19, 2), nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.sysutcdatetime())
    updated_at = Column(DateTime, server_default=func.sysutcdatetime())

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


# -------------------------
# OrderItem Model
# -------------------------
class OrderItem(Base):
    __tablename__ = "OrderItem"

    order_item_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    order_id = Column(UNIQUEIDENTIFIER, ForeignKey("Orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UNIQUEIDENTIFIER, ForeignKey("Product.product_id", ondelete="NO ACTION"), nullable=False)
    supplier_id = Column(UNIQUEIDENTIFIER, ForeignKey("Supplier.supplier_id", ondelete="NO ACTION"), nullable=False)

    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(19, 2), nullable=False)
    total_price = Column(DECIMAL(30, 2), Computed("quantity * price")  )  # ✅ computed


    created_at = Column(DateTime, server_default=func.sysutcdatetime())
    updated_at = Column(DateTime, server_default=func.sysutcdatetime())

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    supplier = relationship("Supplier", back_populates="order_items")

# -------------------------
# Payment Model
# -------------------------

class Payment(Base):
    __tablename__ = "Payment"

    payment_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    razorpay_order_id = Column(String(100), nullable=False, unique=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    bill_id = Column(UNIQUEIDENTIFIER, ForeignKey("Bill.bill_id", ondelete="NO ACTION", onupdate="NO ACTION"), nullable=True)
    store_id = Column(UNIQUEIDENTIFIER, ForeignKey("MedicalStore.store_id", ondelete="NO ACTION", onupdate="NO ACTION"), nullable=True)
    customer_id = Column(UNIQUEIDENTIFIER, ForeignKey("Customer.customer_id", ondelete="NO ACTION", onupdate="NO ACTION"), nullable=True)

    amount = Column(DECIMAL(18, 2), nullable=False)
    currency = Column(String(10), default="INR")
    payment_status = Column(String(50), nullable=False, default="created")
    payment_method = Column(String(50), nullable=True)
    description = Column(String, nullable=True)

    is_refunded = Column(Boolean, default=False)
    refund_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.sysdatetime())
    updated_at = Column(DateTime(timezone=True), onupdate=func.sysdatetime(), server_default=func.sysdatetime())
# -----------------------------
# Plan Table
# -----------------------------
class Plan(Base):
    __tablename__ = "plans"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)  # amount in INR
    interval = Column(String(20), default="month")  # "month", "year", etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    subscriptions = relationship("Subscription", back_populates="plan")


# -----------------------------
# Subscription Table
# -----------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.id"), nullable=False)
    plan_id = Column(UNIQUEIDENTIFIER, ForeignKey("plans.id"), nullable=False)
    razorpay_subscription_id = Column(String(100), unique=True, nullable=False)
    razorpay_plan_id = Column(String(100), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.created)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    user = relationship("User", back_populates="subscriptions")


# -------------------------
# Store Settings
# -------------------------
class StoreSettings(Base):
    __tablename__ = "StoreSettings"

    store_settings_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)

    accepts_online_orders = Column(Boolean, nullable=False, default=True)   # bit
    notif_on_low_stock = Column(Boolean, nullable=False, default=True)      # bit
    low_stock_threshold = Column(Integer, nullable=False, default=5)        # int

    created_at = Column(DateTime(timezone=True), server_default=func.now())  # datetime2

    # Relationship
    store = relationship("MedicalStore", back_populates="settings")



# -------------------------
# Audit Log
# -------------------------
class AuditLog(Base):
    __tablename__ = "AuditLog"

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id = Column(String(36), ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), nullable=True)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)


# -------------------------
# Dashboard (FIXED)
# -------------------------
class MedicalStoreDashboard(Base):
    __tablename__ = "vw_MedicalStoreDashboard"  # your SQL Server view
    __table_args__ = {"extend_existing": True, "schema": "dbo"} 

    # dashboard_id is still mapped, but no longer the primary key
    dashboard_id = Column(String(36)) 
    
    # store_id is set as the primary key to load the view row successfully.
    store_id = Column(
        String(36), 
        ForeignKey("MedicalStore.store_id", ondelete="CASCADE"), 
        primary_key=True, # <-- CRITICAL FIX
        nullable=False
    )

    # All metrics are set to nullable=True to handle the COALESCE/NULL behavior.
    # If the SQL view is fixed (using COALESCE), these will return 0.
    total_inventory_items = Column(Integer, nullable=True) # <-- Changed to nullable=True
    total_products = Column(Integer, nullable=True)        # <-- Changed to nullable=True
    total_customers = Column(Integer, nullable=True)       # <-- Changed to nullable=True
    total_suppliers = Column(Integer, nullable=True)       # <-- Changed to nullable=True
    pending_requests = Column(Integer, nullable=True)      # <-- Changed to nullable=True

    last_updated = Column(DateTime, nullable=True)         # <-- Changed to nullable=True

    # Relationship
    store = relationship("MedicalStore", back_populates="dashboard")

    # Prevent accidental writes
    def __init__(self, *args, **kwargs):
        # Allow instantiation during SQLAlchemy loading, but raise for direct user creation
        if not all(k in kwargs for k in ['_sa_instance_state']):
             raise TypeError("MedicalStoreDashboard is a read-only view and cannot be instantiated directly.")
        super().__init__(*args, **kwargs)