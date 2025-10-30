import os

db_user = os.getenv("MSSQL_USER", "sa")
db_pass = os.getenv("SA_PASSWORD", "Niksain@1041MedicalApp2024")
db_host = os.getenv("MSSQL_HOST", "mssql")
db_name = os.getenv("MSSQL_DB", "medicalAppdb")

DATABASE_URL = (
    f"mssql+pyodbc://{db_user}:{db_pass}@{db_host}:1433/{db_name}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes&TrustServerCertificate=yes"
)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

