"""Rotas de autenticação (registro, login, perfil do usuário)."""

from __future__ import annotations

import logging
import secrets
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from endovision.db.database import get_db
from endovision.db.models import User
from endovision.api.schemas import (
    ActivateKeyRequest,
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UserProfile,
)
from endovision.services.auth import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    register_user,
    verify_access_token,
)

logger = logging.getLogger("endovision.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

# Chaves VIP Oficiais (ABO - Associação Brasileira de Odontologia & Korvyn)
VALID_VIP_KEYS = {
    "ABOPRO",
    "ABO-ENDO",
    "ABO2026",
    "ABO-VIP",
    "KORVYNPRO",
    "KORVYN-VIP",
    "CORVINPRO",
}


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Obtém o usuário atual pelo cabeçalho Authorization Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    payload = verify_access_token(token)
    if not payload:
        return None

    user_id = int(payload.get("sub", 0))
    return get_user_by_id(db, user_id)


def require_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Exige usuário autenticado ou lança 401 Unauthorized."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Por favor, faça login.",
        )
    return current_user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Cadastra um novo usuário no sistema."""
    try:
        user = register_user(db, req.name, req.email, req.password)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    token = create_access_token(user.id, user.email, user.plan)
    return AuthResponse(
        user=UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            plan=user.plan,
            is_pro=user.is_pro(),
        ),
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Autentica o usuário e retorna o token de acesso."""
    user = authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    token = create_access_token(user.id, user.email, user.plan)
    return AuthResponse(
        user=UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            plan=user.plan,
            is_pro=user.is_pro(),
        ),
        token=token,
    )


@router.get("/me", response_model=UserProfile)
def get_me(user: User = Depends(require_user)):
    """Retorna o perfil do usuário logado e status do plano."""
    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        plan=user.plan,
        is_pro=user.is_pro(),
    )


@router.post("/activate-key", response_model=AuthResponse)
def activate_key(
    req: ActivateKeyRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Ativa uma chave VIP promocional (ex: ABO - Associação Brasileira de Odontologia)."""
    clean_key = req.key.strip().upper()
    if clean_key not in VALID_VIP_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chave inválida ou expirada. Verifique com a coordenação da ABO ou suporte Korvyn.",
        )

    # Concede plano Pro Vitalício para testes e validação da ABO
    user.plan = "pro_lifetime"
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email, user.plan)
    return AuthResponse(
        user=UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            plan=user.plan,
            is_pro=user.is_pro(),
        ),
        token=token,
    )


@router.post("/google", response_model=AuthResponse)
def google_auth(
    req: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """Autentica ou cadastra o dentista via Google Sign-In com validação do ID token."""
    try:
        # Validação do ID Token diretamente na API de tokens do Google
        verify_url = "https://oauth2.googleapis.com/tokeninfo"
        resp = httpx.get(verify_url, params={"id_token": req.credential}, timeout=10.0)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Google inválido ou expirado.",
            )

        google_data = resp.json()
        email = google_data.get("email")
        name = google_data.get("name", "Dentista")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail do Google não encontrado.",
            )

        clean_email = email.strip().lower()
        user = get_user_by_email(db, clean_email)

        # Se for novo usuário, cadastra automaticamente
        if not user:
            initial_plan = "free"
            if req.referral_key and req.referral_key.strip().upper() in VALID_VIP_KEYS:
                initial_plan = "pro_lifetime"

            user = User(
                name=name,
                email=clean_email,
                password_hash=hash_password(secrets.token_hex(16)),
                plan=initial_plan,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Se já existia e passou uma chave ABO, ativa Pro caso ainda não seja
            if req.referral_key and req.referral_key.strip().upper() in VALID_VIP_KEYS and not user.is_pro():
                user.plan = "pro_lifetime"
                db.commit()
                db.refresh(user)

        token = create_access_token(user.id, user.email, user.plan)
        return AuthResponse(
            user=UserProfile(
                id=user.id,
                name=user.name,
                email=user.email,
                plan=user.plan,
                is_pro=user.is_pro(),
            ),
            token=token,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro no Google Auth: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na autenticação Google: {str(exc)}",
        )
