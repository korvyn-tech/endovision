"""Testes automatizados para autenticação e gerenciamento de usuários."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from endovision.api.main import app
from endovision.db.database import Base, get_db
from endovision.db.models import User
from endovision.services.auth import (
    authenticate_user,
    create_access_token,
    hash_password,
    register_user,
    verify_access_token,
    verify_password,
)

from sqlalchemy.pool import StaticPool

# Banco SQLite em memória com StaticPool para compartilhar conexão
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_password_hashing_and_verification():
    raw = "SenhaForte123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("SenhaErrada", hashed) is False


def test_jwt_token_flow():
    token = create_access_token(user_id=42, email="dr.silva@clinica.com", plan="free")
    assert isinstance(token, str)
    payload = verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "dr.silva@clinica.com"
    assert payload["plan"] == "free"

    # Token inválido
    assert verify_access_token("token.invalido.falso") is None


def test_register_and_authenticate_user(db_session):
    user = register_user(db_session, "Dra. Carolina", "carolina@endo.com", "segredo123")
    assert user.id is not None
    assert user.name == "Dra. Carolina"
    assert user.email == "carolina@endo.com"
    assert user.plan == "free"
    assert user.is_pro() is False

    # Login com sucesso
    authenticated = authenticate_user(db_session, "carolina@endo.com", "segredo123")
    assert authenticated is not None
    assert authenticated.id == user.id

    # Login com senha incorreta
    assert authenticate_user(db_session, "carolina@endo.com", "senha_errada") is None

    # Tentativa de duplicar e-mail
    with pytest.raises(ValueError, match="Já existe um usuário"):
        register_user(db_session, "Outra Carolina", "carolina@endo.com", "outrasenha")


def test_api_auth_endpoints(client):
    # 1. Registro via API
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Dr. Roberto", "email": "roberto@endo.com", "password": "clinica1234"},
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "token" in data
    assert data["user"]["name"] == "Dr. Roberto"
    assert data["user"]["plan"] == "free"
    token = data["token"]

    # 2. Login via API
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "roberto@endo.com", "password": "clinica1234"},
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()

    # 3. Rota protegida /me com token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "roberto@endo.com"
    assert me_data["is_pro"] is False

    # 4. Rota protegida /me sem token
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


def test_activate_vip_key_abo(client):
    # 1. Registra usuário
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Dr. Fernando ABO", "email": "fernando@abo.org.br", "password": "senhaforte123"},
    )
    token = reg_res.json()["token"]
    assert reg_res.json()["user"]["is_pro"] is False

    # 2. Ativa chave ABO
    act_res = client.post(
        "/api/v1/auth/activate-key",
        json={"key": "ABOPRO"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["user"]["plan"] == "pro_lifetime"
    assert act_data["user"]["is_pro"] is True

    # 3. Chave inválida retorna 400
    inv_res = client.post(
        "/api/v1/auth/activate-key",
        json={"key": "CHAVE_INEXISTENTE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert inv_res.status_code == 400


def test_google_auth_endpoint(client):
    from unittest.mock import patch, MagicMock

    mock_google_resp = MagicMock(status_code=200)
    mock_google_resp.json.return_value = {
        "email": "dr.marcos.google@clinica.com",
        "name": "Dr. Marcos Google",
        "email_verified": "true",
    }

    with patch("httpx.get", return_value=mock_google_resp):
        res = client.post(
            "/api/v1/auth/google",
            json={"credential": "mock_valid_google_jwt_token", "referral_key": "ABO2026"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["email"] == "dr.marcos.google@clinica.com"
        assert data["user"]["name"] == "Dr. Marcos Google"
        assert data["user"]["plan"] == "pro_lifetime"
        assert data["user"]["is_pro"] is True
        assert "token" in data
