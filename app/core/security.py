from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt
from pydantic import ValidationError

from app.core.config import get_settings

settings = get_settings()

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if isinstance(password, str):
        password = password.encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except (jwt.JWTError, ValidationError):
        return None


def get_token_expiry(expires_delta: Optional[timedelta] = None) -> datetime:
    if expires_delta:
        return datetime.now(timezone.utc) + expires_delta
    return datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)