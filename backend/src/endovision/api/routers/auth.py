"""Rotas de autenticação (registro, login, perfil do usuário)."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from endovision.db.database import get_db
from endovision.db.models import User
from endovision.api.schemas import AuthResponse, LoginRequest, RegisterRequest, UserProfile
from endovision.services.auth import (
    authenticate_user,
    create_access_token,
    get_user_by_id,
    register_user,
    verify_access_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


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
