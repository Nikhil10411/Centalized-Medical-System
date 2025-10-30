#!/usr/bin/env bash
set -euo pipefail

# ✅ Load DB env variables (NO hard-coding)
# These variables must be defined in your .env file
DB_HOST="${DB_HOST}"
DB_PORT="${DB_PORT}"
DB_USER="${DB_USER}"
DB_PASS="${DB_PASSWORD}"
DB_NAME="${DB_NAME}"
ODBC_DRIVER="ODBC Driver 18 for SQL Server"

RETRY_COUNT=30
SLEEP_SECONDS=4

echo "⏳ Waiting for SQL Server at $DB_HOST:$DB_PORT ..."

# Use python and pyodbc to wait for the database connection to be fully ready
i=0
until [ $i -ge $RETRY_COUNT ]; do
  # Python script attempts to connect using pyodbc
  python3 - <<PY
import os, sys
try:
    import pyodbc
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db = os.getenv("DB_NAME")
    driver = "ODBC Driver 18 for SQL Server"

    # Connection string includes TrustServerCertificate=yes to handle self-signed cert
    conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};UID={user};PWD={password};TrustServerCertificate=yes"
    conn = pyodbc.connect(conn_str, timeout=3)
    conn.close()
    sys.exit(0)
except:
    sys.exit(1)
PY

  if [ $? -eq 0 ]; then
    echo "✅ SQL Server is ready"
    break
  fi

  i=$((i+1))
  echo "Retry ${i}/${RETRY_COUNT} — waiting ${SLEEP_SECONDS}s..."
  sleep "${SLEEP_SECONDS}"
done

if [ $i -ge $RETRY_COUNT ]; then
  echo "❌ DB not reachable — exiting"
  exit 1
fi

echo "📦 Ensuring database '$DB_NAME' exists..."
# FIX: Using the standard '/opt/mssql-tools/bin/sqlcmd' path and adding the '-C' (TrustServerCertificate) flag.
/opt/mssql-tools/bin/sqlcmd -S "$DB_HOST,$DB_PORT" -U "$DB_USER" -P "$DB_PASS" -C \
-Q "IF NOT EXISTS(SELECT name FROM sys.databases WHERE name = '$DB_NAME') CREATE DATABASE [$DB_NAME];"

echo "⚙️ Running Alembic migrations..."
alembic upgrade head || { echo "🔴 Alembic failed"; exit 1; }

echo "🚀 Starting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
