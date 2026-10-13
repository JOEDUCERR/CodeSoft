import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")

def hash_password(password: str) -> str: return password_hash.hash(password)
def verify_password(password: str, hashed: str) -> bool: return password_hash.verify(password, hashed)
def create_access_token(user_id: str, role: str) -> str:
    return jwt.encode({"sub": user_id, "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "1440")))}, JWT_SECRET, algorithm="HS256")
def decode_access_token(token: str) -> dict: return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
