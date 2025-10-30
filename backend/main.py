from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session
from database import get_db, SessionLocal, engine, Base
from routers import (
    auth, medical_store, patients, 
    doctors, medical_history, cart, 
    payment, subscription
)
from models import User
from utils.utils import hash_password

from dotenv import load_dotenv
import os
import uuid
from fastapi_pagination import add_pagination



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

# ✅ CORS middleware (adjust origins in production)
# ✅ CORS middleware (updated and permanent)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1/8000"
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
app.include_router(medical_store.router, prefix="/medical_store", tags=["Medical Store"])
# app.include_router(pharmacy.router, prefix="/pharmacy", tags=["Pharmacy"])
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])
app.include_router(payment.router, prefix="/api", tags=["Payment"])


# ✅ Admin user creation logic
def create_admin_user():
    db = SessionLocal()
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not all([admin_email, admin_username, admin_password]):
        print("⚠️ Admin credentials not set in .env")
        return

    if not db.query(User).filter(User.email == admin_email).first():
        new_admin = User(
            id=str(uuid.uuid4()),
            username=admin_username,
            email=admin_email,
            hashed_password=hash_password(admin_password),
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        print("✅ Admin user created.")
    else:
        print("ℹ️ Admin user already exists.")

# ✅ Startup logic
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
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
        return db.execute("SELECT * FROM Items").fetchall()
    except Exception as e:
        return {"error": str(e)}

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


@app.get("/health/db")
def check_db(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}