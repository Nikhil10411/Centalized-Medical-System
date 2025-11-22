from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_URL = os.getenv("connection_url")
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES"))

settings = Settings()
