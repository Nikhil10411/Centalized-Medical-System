from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session
# New imports for robust startup logic
from sqlalchemy.exc import ProgrammingError 
from sqlalchemy import text # Added for the /health/db endpoint
import time
# End new imports

from database import get_db, SessionLocal, engine, Base
from routers import (
    auth, medical_store, patients, 
    doctors, medical_history, cart, 
    payment, subscription
)
from models import User # NOTE: Ensure User model has __table_args__ = {"schema": "dbo"}
from utils.utils import hash_password

from dotenv import load_dotenv
import os
import uuid
from fastapi_pagination import add_pagination


# Configuration for the DDL commitment retry loop
MAX_RETRIES = 30 # Increased retries just in case, though the fix should be immediate
RETRY_DELAY_SECONDS = 5 # Reduced delay slightly

# ✅ Load environment variables
load_dotenv()

# ✅ Create FastAPI app
app = FastAPI(
    title="MedicalApp API",
    description="A secure medical service API with role-based access",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

add_pagination(app)

# ✅ Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# ✅ CORS middleware (updated and permanent)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  
        "http://127.0.0.1:3000",
        "http://medical-frontend:3000", 
        "http://localhost:8000",   
        "http://127.0.0.1:8000",
        "http://medical-backend:8000", 
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods
    allow_headers=["*"],   # Allow all headers
)

# ✅ Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(doctors.router, prefix="/api", tags=["Doctor"])
app.include_router(patients.router, prefix="/api", tags=["Patient"])
app.include_router(medical_history.router, prefix="/api", tags=["Medical History"])
app.include_router(cart.router, prefix="/api", tags=["Cart"])
#app.include_router(otp_auth.router, prefix="/otp_auth", tags=["Otp_auth"])
#app.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals"])
#app.include_router(hospital_staffs.router, prefix="/hospital_staff", tags=["Hospital Staff"])
#app.include_router(hospital_admin.router, prefix="/hospital_admin", tags=["Hospital Admin"])
#app.include_router(doctor_verification.router, prefix="/doctor_verification", tags=["Doctor Verification"])
app.include_router(medical_store.router, prefix="/api/medical_store", tags=["Medical Store"])
# app.include_router(pharmacy.router, prefix="/pharmacy", tags=["Pharmacy"])
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])
app.include_router(payment.router, prefix="/api", tags=["Payment"])


# ✅ Table existence check (replaces fixed sleep)
def wait_for_users_table():
    """
    Aggressively checks for the existence of the 'dbo.users' table using raw SQL.
    This is the most reliable way to overcome MSSQL's DDL visibility delay.
    """
    print("⏳ Starting aggressive wait for 'dbo.users' table visibility...")
    for attempt in range(MAX_RETRIES):
        db = SessionLocal()
        try:
            # --- CRITICAL FIX: Use raw SQL with explicit schema (dbo.users) ---
            # This minimal query forces MSSQL to find the object by its fully 
            # qualified name, bypassing ORM generation issues.
            db.execute(text("SELECT 1 FROM dbo.users WHERE 1 = 0"))
            db.commit() # Commit/end transaction to ensure visibility
            # ------------------------------------------------------------------
            
            print("✅ 'dbo.users' table is visible and ready.")
            db.close()
            return
        
        except ProgrammingError as e:
            # Check for the specific 'Invalid object name' error (Error code 208 for MSSQL)
            if "Invalid object name" in str(e) and ("(208)" in str(e) or "'dbo.users'" in str(e)):
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Attempt {attempt + 1}/{MAX_RETRIES}: Table 'dbo.users' not yet visible. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    db.rollback()
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    db.close()
                    print(f"❌ Failed to see 'dbo.users' table after {MAX_RETRIES} attempts. Startup aborted.")
                    raise ConnectionError("Database table 'users' did not become visible within the allowed retry window.") from e
            else:
                db.close()
                raise e # Raise other ProgrammingErrors

        except Exception as e:
            db.close()
            # If the database connection itself fails, retry.
            print(f"⚠️ Attempt {attempt + 1}/{MAX_RETRIES}: Generic error during check: {str(e)}. Retrying in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)

# ✅ Admin user creation logic (Cleaned up, no internal wait/retry needed)
def create_admin_user():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not all([admin_email, admin_username, admin_password]):
        print("⚠️ Admin credentials not set in .env")
        return

    db = SessionLocal()
    try:
        # Now that the table is guaranteed to be visible via the check above, 
        # the ORM query below should succeed.
        if not db.query(User).filter(User.email == admin_email).first():
            new_admin = User(
                # Only include ID if your model specifies it as a string/UUID and not auto-incrementing
                # id=str(uuid.uuid4()), 
                username=admin_username,
                email=admin_email,
                hashed_password=hash_password(admin_password),
                is_admin=True
            )
            db.add(new_admin)
            db.commit()
            print("✅ Admin user created successfully.")
        else:
            print("ℹ️ Admin user already exists.")
        
        db.close()

    except Exception as e:
        db.close()
        print(f"❌ Failed to create admin user: {str(e)}")
        # Note: If the table check failed, the code would have already aborted/crashed
        raise e

# ✅ Startup logic
@app.on_event("startup")
def on_startup():
    # 1. Create all tables (DDL issued) - Redundant if Alembic is used, but harmless.
    Base.metadata.create_all(bind=engine)
    
    # 2. WAIT for the tables to be visible before proceeding
    wait_for_users_table()
    
    # 3. Create admin user (now guaranteed the table exists)
    create_admin_user()

# ✅ Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the MedicalApp API"}

# ✅ Health check (for Docker/Kubernetes/etc.)
@app.get("/healthz", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}

# ✅ Optional DB test route (delete if not used)
@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    try:
        # NOTE: Using dbo.Items assuming all tables are in the dbo schema
        return db.execute(text("SELECT * FROM dbo.Items")).fetchall()
    except Exception as e:
        return {"error": str(e)}

# ✅ Health check for DB
@app.get("/health/db")
def check_db(db=Depends(get_db)):
    try:
        # Use a simple, schema-independent query
        db.execute(text("SELECT 1")) 
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ✅ Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Invalid input",
            "details": exc.errors()
        },
    )

# ✅ General HTTPException handler
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )

# ✅ OpenAPI debug endpoint
@app.get("/debug-openapi")
def debug_openapi():
    return app.openapi()
