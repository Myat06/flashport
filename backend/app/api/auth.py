import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.operator import Operator

router = APIRouter(prefix="/auth", tags=["auth"])

_ALGORITHM = "HS256"


def _pin_hash(pin: str) -> str:
    return hashlib.sha256(f"{settings.secret_key}:{pin}".encode()).hexdigest()


def _pin_verify(pin: str, stored_hash: str) -> bool:
    return _pin_hash(pin) == stored_hash


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OperatorLoginRequest(BaseModel):
    employee_id: str
    pin: str


class OperatorLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee_id: str
    name: str


def create_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.secret_key,
        algorithm=_ALGORITHM,
    )


def verify_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return True
    except Exception:
        return False


def hash_pin(pin: str) -> str:
    return _pin_hash(pin)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if (
        body.username != settings.manager_username
        or body.password != settings.manager_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(body.username))


@router.post("/operator/login", response_model=OperatorLoginResponse)
def operator_login(body: OperatorLoginRequest, db: Session = Depends(get_db)):
    operator = (
        db.query(Operator)
        .filter(Operator.employee_id == body.employee_id, Operator.is_active == True)  # noqa: E712
        .first()
    )
    if not operator or not _pin_verify(body.pin, operator.pin_hash):
        raise HTTPException(status_code=401, detail="Invalid employee ID or PIN")
    return OperatorLoginResponse(
        access_token=create_token(operator.employee_id),
        employee_id=operator.employee_id,
        name=operator.name,
    )
