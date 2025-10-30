#!/bin/bash
set -e

# Start SQL Server in background
/opt/mssql/bin/sqlservr &

echo "⏳ Waiting for SQL Server to become available..."

RETRIES=30
until /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -Q "SELECT 1" -C > /dev/null 2>&1; do
  if [ $RETRIES -le 0 ]; then
    echo "❌ ERROR: SQL Server never became ready in time."
    exit 1
  fi
  echo "Retry $((30 - RETRIES + 1)): SQL Server not ready yet..."
  sleep 5
  ((RETRIES--))
done

echo "✅ SQL Server is up."

# Run initialization SQL or migrations as needed
if [ -f "/docker/init_db.sql" ]; then
  echo "📄 Running init_db.sql script..."
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -i /docker/init_db.sql -C || {
    echo "❌ Failed to run init_db.sql"
    exit 1
  }
else
  echo "ℹ️ init_db.sql not found, skipping..."
fi

echo "⚙️ Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
