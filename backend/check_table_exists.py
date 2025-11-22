from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
import os
import sys

# Load .env variables
load_dotenv()

# ✅ Use standard variable name
DATABASE_URL = os.getenv("connection_url") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL / connection_url not found in environment.")
    sys.exit(1)

SCHEMA_NAME = "dbo"

# ✅ Define tables expected after Alembic migration
required_tables = [
    "users", "hospitals", "departments", "rooms", "services", "doctors", 
    "doctor_duties", "hospital_staff", "patients", "appointments",
    "medical_history", "doctor_verification", "alembic_version"
]

def verify_tables():
    print("\n--- Checking Database Schema ---")

    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        db_tables = inspector.get_table_names(schema=SCHEMA_NAME)

        print(f"📦 Found {len(db_tables)} tables in '{SCHEMA_NAME}':")
        for table in sorted(db_tables):
            print(f"   - {table}")

        missing = [t for t in required_tables if t not in db_tables]

        if missing:
            print("\n❌ Missing tables:")
            for t in missing:
                print(f"   - {t}")
            print("\n❗ Alembic migration did not create all tables!")
            sys.exit(1)

        print("\n✅ All required tables exist! Database schema verified.\n")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ DB Schema Verification Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_tables()

