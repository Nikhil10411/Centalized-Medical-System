from sqlalchemy import create_engine
from database import engine, Base
from models import User  # Import models to create tables

# Create all tables in the database
Base.metadata.create_all(bind=engine)
