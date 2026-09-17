from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import os
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Argon2id hasher instance (OWASP recommended parameters)
_ph = PasswordHasher()

# Pre-computed dummy hash to mitigate timing attacks on nonexistent user lookups
_DUMMY_HASH = _ph.hash("dummy_constant_time_password_salt_mitigation")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-key-change-in-production-1234567890")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h default
ACCESS_TOKEN_EXPIRE_SECONDS = ACCESS_TOKEN_EXPIRE_MINUTES * 60


def hash_password(password: str) -> str:
    """Hash a password using Argon2id with automatic salt generation."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2id hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_verify_password(plain_password: str) -> bool:
    """
    Perform a dummy Argon2id verification when a user is not found
    to ensure constant response times and prevent user enumeration timing attacks.
    """
    try:
        _ph.verify(_DUMMY_HASH, plain_password)
    except Exception:
        pass
    return False


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
