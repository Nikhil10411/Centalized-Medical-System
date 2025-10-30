import os
import sys
from logging.config import fileConfig
from pathlib import Path
import configparser

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Setup paths and load .env
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent                        # Niksain/
sys.path.append(str(BASE_DIR))                    # Add backend/ to sys.path

dotenv_path = ROOT_DIR / ".env"
if not dotenv_path.exists():
    raise FileNotFoundError(f"❌ Missing .env file at {dotenv_path}")
load_dotenv(dotenv_path)

# ─────────────────────────────────────────────
# Alembic Config
# ─────────────────────────────────────────────
config = context.config

# Disable interpolation to handle special chars in DB URL
raw_config = configparser.ConfigParser(interpolation=None)
with open(config.config_file_name) as f:
    raw_config.read_file(f)
config.file_config = raw_config

# Load connection URL from .env
conn_str = os.getenv("connection_url")
if not conn_str:
    raise RuntimeError("❌ Environment variable 'connection_url' is not set or empty")
config.set_main_option("sqlalchemy.url", conn_str)

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─────────────────────────────────────────────
# Import models.Base
# ─────────────────────────────────────────────
try:
    from models import Base
except ImportError as e:
    print("❌ Error importing Base from models.py")
    raise e

target_metadata = Base.metadata

# ─────────────────────────────────────────────
# Offline mode (generates SQL)
# ─────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = os.getenv("connection_url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# ─────────────────────────────────────────────
# Online mode (apply migrations)
# ─────────────────────────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

# ─────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
