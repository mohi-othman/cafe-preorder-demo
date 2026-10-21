"""Staff logins: bcrypt passwords, JWTs carrying role and Café, and route guards.

Protected routes depend on `require_admin` (Super Admin) or `require_barista` (returns the Barista's Café).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.menu import CafeOut
from app.models import Cafe, User

ADMIN = "admin"
BARISTA = "barista"
Role = Literal["admin", "barista"]

TOKEN_LIFETIME = timedelta(hours=12)  # one shift
ALGORITHM = "HS256"


class InvalidToken(ValueError):
    pass


@dataclass(frozen=True)
class Claims:
    user_id: int
    role: str
    cafe_id: int | None
    expires_at: datetime | None = None


MAX_PASSWORD_BYTES = 72  # bcrypt's limit, in UTF-8 bytes; longer passwords make bcrypt raise


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode()) > MAX_PASSWORD_BYTES:  # can't have been set, so it can't match
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, role: str, cafe_id: int | None, secret: str, now: datetime) -> str:
    payload = {"sub": str(user_id), "role": role, "cafe_id": cafe_id, "iat": now, "exp": now + TOKEN_LIFETIME}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str, now: datetime) -> Claims:
    try:
        # PyJWT checks "exp" against the wall clock, so check it against `now` here instead.
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"verify_exp": False, "require": ["exp"]})
        if payload["exp"] <= now.timestamp():
            raise InvalidToken("token expired")
        return Claims(
            user_id=int(payload["sub"]), role=payload["role"], cafe_id=payload.get("cafe_id"),
            expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as e:
        raise InvalidToken(str(e)) from e


def _secret() -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not set (env var or src/api/.env)")
    return settings.jwt_secret


_bearer = HTTPBearer(auto_error=False)


def current_claims(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Claims:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not logged in", headers={"WWW-Authenticate": "Bearer"})
    try:
        return decode_token(credentials.credentials, _secret(), now=datetime.now(timezone.utc))
    except InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})


def require_admin(claims: Claims = Depends(current_claims)) -> Claims:
    if claims.role != ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin only")
    return claims


def require_barista_claims(claims: Claims = Depends(current_claims)) -> Claims:
    if claims.role != BARISTA or claims.cafe_id is None:
        raise HTTPException(status_code=403, detail="Barista only")
    return claims


def require_barista(claims: Claims = Depends(require_barista_claims), session: Session = Depends(get_session)) -> Cafe:
    """The logged-in Barista's Café. Always take the Café from here, never from the request."""
    cafe = session.get(Cafe, claims.cafe_id)
    if cafe is None:
        raise HTTPException(status_code=401, detail="Café no longer exists")
    return cafe


router = APIRouter(prefix="/api/auth")


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    cafe: CafeOut | None


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == body.username.strip())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    cafe = session.get(Cafe, user.cafe_id) if user.cafe_id is not None else None
    token = create_token(user.id, user.role, user.cafe_id, _secret(), now=datetime.now(timezone.utc))
    return LoginOut(
        access_token=token, role=user.role,
        cafe=CafeOut.model_validate(cafe, from_attributes=True) if cafe else None,
    )
