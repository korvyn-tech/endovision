"""Serviço de autenticação, criptografia de senhas e tokens de sessão."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from endovision.db.models import User

# Configurações de segurança
JWT_SECRET = os.getenv("JWT_SECRET", "korvyn_endovision_secure_jwt_secret_default_key_2026")
JWT_ALGORITHM = "HS256"
DEFAULT_EXPIRATION_HOURS = 24 * 30  # 30 dias


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def hash_password(password: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 com salt aleatório."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha plana confere com o hash armazenado."""
    try:
        salt, expected_hex = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


def create_access_token(user_id: int, email: str, plan: str, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT seguro com assinatura HMAC-SHA256."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=DEFAULT_EXPIRATION_HOURS))

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "email": email,
        "plan": plan,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_access_token(token: str) -> Optional[dict]:
    """Valida assinatura e expiração do JWT. Retorna payload ou None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("exp", 0) < now_ts:
            return None  # Token expirado

        return payload
    except Exception:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por e-mail insensível a maiúsculas/minúsculas."""
    return db.query(User).filter(User.email == email.strip().lower()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Busca usuário pelo identificador numérico."""
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, name: str, email: str, password: str) -> User:
    """Cadastra um novo usuário no banco com plano gratuito inicial."""
    clean_email = email.strip().lower()
    existing = get_user_by_email(db, clean_email)
    if existing:
        raise ValueError("Já existe um usuário cadastrado com este e-mail.")

    if len(password) < 6:
        raise ValueError("A senha deve ter no mínimo 6 caracteres.")

    user = User(
        name=name.strip(),
        email=clean_email,
        password_hash=hash_password(password),
        plan="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autentica usuário com e-mail e senha. Retorna User ou None."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
