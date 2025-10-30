# app/accounts/auth_handlers.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..utils.utils import hash_password, verify_password
from ..database import get_db_connection, close_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def signup_user(user_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(user_data.password)
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user_data.username, hashed_password))
    conn.commit()
    close_db_connection(conn)

def login_user(user_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (user_data.username,))
    user = cursor.fetchone()
    close_db_connection(conn)
    if user and verify_password(user_data.password, user.password_hash):
        token = create_access_token(data={"sub": user_data.username})
        return token
    return None
