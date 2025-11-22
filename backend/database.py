import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# --- 1. Environment and Connection URL Setup ---
# Load environment variables from .env file.
# Note: In a Docker environment, 'dotenv' might not always be the first to load.
# We ensure the path to .env is correct if it's not in the current working directory.
load_dotenv() 

# Fetch the MSSQL connection string from the .env file
# NOTE: Using a fallback to environment variables in case .env loading fails
DATABASE_URL = os.getenv("connection_url") 

if not DATABASE_URL:
    # Use a print statement for visibility if it crashes before logging starts
    print("❌ FATAL ERROR: 'connection_url' environment variable is not set. Check .env file or Docker setup.")
    # Exit gracefully if critical information is missing
    sys.exit(1)

# --- 2. Engine Configuration ---
try:
    # Configure the SQLAlchemy engine
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,           # Maintain up to 10 connections in the pool
        max_overflow=5,         # Allow 5 additional connections beyond the pool size
        pool_timeout=30,        # Wait for 30 seconds before timing out
        pool_recycle=1800,      # Recycle connections after 30 minutes (30 mins)
        echo=True               # Enable SQLAlchemy logging for debugging
    )
except Exception as e:
    print(f"❌ FATAL ERROR: Could not create SQLAlchemy engine: {e}")
    sys.exit(1)


# --- 3. Base and Session Configuration ---
# SessionLocal MUST be defined before Base for proper initialization order.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base must be defined here so that all model classes inheriting from it
# (in your models.py) register their metadata correctly.
Base = declarative_base()


# --- 4. Database Dependency ---
def get_db():
    """Dependency function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
