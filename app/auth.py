from datetime import datetime, timedelta, timezone
import hashlib
import re

from fastapi import Depends, Header, HTTPException, WebSocket, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from app.mongo import get_users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not EMAIL_REGEX.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address.",
        )
    return normalized


def validate_password(password: str) -> str:
    value = password or ""
    if len(value) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long.",
        )
    return value


def hash_password(password: str):
    password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str, email: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_user(email: str, password: str):
    normalized_email = normalize_email(email)
    password_value = validate_password(password)
    try:
        collection = get_users_collection()
        document = {
            "email": normalized_email,
            "password_hash": hash_password(password_value),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User database is currently unavailable.",
        ) from exc

    document["_id"] = result.inserted_id
    return {
        "id": str(document["_id"]),
        "email": document["email"],
    }


def authenticate_user(email: str, password: str):
    normalized_email = normalize_email(email)
    password_value = validate_password(password)
    try:
        collection = get_users_collection()
        user = collection.find_one({"email": normalized_email})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User database is currently unavailable.",
        ) from exc
    if not user or not verify_password(password_value, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return {
        "id": str(user["_id"]),
        "email": user["email"],
    }


def _unauthorized_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise _unauthorized_exception() from exc

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise _unauthorized_exception()
    return {
        "id": user_id,
        "email": email,
    }


def get_current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise _unauthorized_exception()

    token = authorization.split(" ", 1)[1].strip()
    token_payload = decode_token(token)

    try:
        collection = get_users_collection()
        user = collection.find_one({"email": token_payload["email"]})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User database is currently unavailable.",
        ) from exc
    if not user:
        raise _unauthorized_exception()

    return {
        "id": str(user["_id"]),
        "email": user["email"],
    }


def get_websocket_user(websocket: WebSocket):
    auth_header = websocket.headers.get("authorization", "")
    query_token = websocket.query_params.get("token", "").strip()

    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif query_token:
        token = query_token

    if not token:
        raise _unauthorized_exception()

    token_payload = decode_token(token)
    try:
        collection = get_users_collection()
        user = collection.find_one({"email": token_payload["email"]})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User database is currently unavailable.",
        ) from exc
    if not user:
        raise _unauthorized_exception()

    return {
        "id": str(user["_id"]),
        "email": user["email"],
    }
