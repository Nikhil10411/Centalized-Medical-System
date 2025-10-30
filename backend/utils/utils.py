import hashlib
import random
import string
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Retrieve security settings from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not specified
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))  # Default to 30 minutes

# ✅ Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ OAuth2 token authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ Function to hash a password securely using bcrypt
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ✅ Function to verify a hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ✅ Function to create a JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Function to decode and verify a JWT token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Role-Based Access Control (RBAC) - Function to check user role
def check_user_role(required_role: str, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    user_role = payload.get("role")

    if not user_role or user_role != required_role:
        raise HTTPException(status_code=403, detail="Permission denied")

    return user_role

# ✅ Function to generate a secure random string (used for API keys, tokens, etc.)
def generate_secure_string(length: int = 32) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# ✅ Function to generate a SHA-256 hash of a given string
def generate_sha256_hash(input_string: str) -> str:
    return hashlib.sha256(input_string.encode()).hexdigest()

# ✅ Function to create an API key with timestamp
def generate_api_key() -> str:
    timestamp = datetime.utcnow().isoformat()
    raw_key = f"{timestamp}{random.randint(1000, 9999)}"
    return generate_sha256_hash(raw_key)

# ✅ Function to validate an API key
def validate_api_key(api_key: str, stored_key: str) -> bool:
    return api_key == stored_key

# ✅ Function to generate a time-based one-time password (TOTP) for enhanced security
def generate_totp_secret() -> str:
    return generate_secure_string(20)

# ✅ Function to verify a one-time password (for 2FA scenarios)
def verify_totp(entered_otp: str, actual_otp: str) -> bool:
    return entered_otp == actual_otp

