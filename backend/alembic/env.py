import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv
import logging
import configparser
import importlib.util # <-- NEW IMPORT

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- 🟢 CRITICAL LOGGING FIX START 🟢 ---
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
logging.getLogger('alembic').setLevel(logging.DEBUG)
print("✅ Logging forced to DEBUG for SQLAlchemy engine and Alembic.")
# --- 🟢 CRITICAL LOGGING FIX END 🟢 ---


# --- CUSTOM PROJECT SETUP ---

# 1. We rely on direct path import now, not sys.path.append

# --- 2. 💥 CRITICAL DIRECT FILE IMPORT FIX 💥 ---

# ⚠️ YOU MUST CONFIRM THIS PATH IS CORRECT INSIDE YOUR DOCKER CONTAINER ⚠️
# Assumes models file is named 'models.py' in the project root (/app)
MODELS_FILE_PATH = Path(__file__).parent.parent / "models.py" 

if not MODELS_FILE_PATH.exists():
    print(f"❌ CRITICAL ERROR: Model file not found at expected path: {MODELS_FILE_PATH}")
    sys.exit(1)

try:
    # Use importlib.util to load the model file directly by its path
    spec = importlib.util.spec_from_file_location("models_module_fix", MODELS_FILE_PATH)
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)
    
    # Get the Base object from the loaded module
    Base = models_module.Base
    print(f"✅ Successfully loaded models from {MODELS_FILE_PATH}")

except Exception as e:
    print(f"❌ Fatal Error during direct model import: {e}")
    sys.exit(1)


# This is the Alembic Config object
config = context.config

if config.config_file_name is not None:
    # 🟢 CRITICAL CONFIG FIX: Manually load alembic.ini to disable interpolation.
    
    file_config = configparser.ConfigParser(interpolation=None)
    file_config.read(config.config_file_name)
    fileConfig(file_config)
    config.file_config = file_config

# Set target_metadata
target_metadata = Base.metadata

# --- CUSTOM .ENV FILE & URL RESOLUTION START ---

alembic_dir = Path(__file__).parent
dotenv_path = alembic_dir.parent / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env file from {dotenv_path}")
else:
    # The existing output shows this:
    print(f"⚠️ Warning: .env file not found at /app/.env. Relying on system environment.") 

CONNECTION_URL = os.environ.get("CONNECTION_URL") 

if CONNECTION_URL:
    config.set_main_option("sqlalchemy.url", CONNECTION_URL)
    print("✅ Using CONNECTION_URL from environment.")
else:
    print("Warning: 'CONNECTION_URL' environment variable not found. Using URL from alembic.ini.")

# --- CUSTOM .ENV FILE & URL RESOLUTION END ---


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (Synchronous for pyodbc)."""
    
    connectable = engine_from_config( 
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        
        # CRITICAL FIX FOR MSSQL DDL VISIBILITY
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            transactional_ddl=False  
        )

        with context.begin_transaction():
            context.run_migrations()


# --- EXECUTION MODE ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()