from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch the MSSQL connection string from the .env file
DATABASE_URL = os.getenv("connection_url")

if not DATABASE_URL:
    raise ValueError("connection_url is not set in the .env file")

# Configure the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Maintain up to 10 connections in the pool
    max_overflow=5,         # Allow 5 additional connections beyond the pool size
    pool_timeout=30,        # Wait for 30 seconds before timing out
    pool_recycle=1800,      # Recycle connections after 30 minutes
    echo=True               # Enable SQLAlchemy logging for debugging
)

# Create SessionLocal for FastAPI
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
