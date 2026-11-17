"""Testes automatizados para cobrança Asaas (Pix, Assinaturas, Webhook e Liberação Pro)."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from endovision.api.main import app
from endovision.db.database import Base, get_db
from endovision.db.models import User, PaymentOrder
from endovision.services.auth import create_access_token, register_user

from sqlalchemy.pool import StaticPool

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


@pytest.fixture(scope="function")
def auth_header(db_session):
    user = register_user(db_session, "Dra. Marina", "marina@endo.com", "senha12345")
    token = create_access_token(user.id, user.email, user.plan)
    return {"Authorization": f"Bearer {token}"}, user


def test_create_order_lifetime_pix(client, auth_header):
    headers, user = auth_header

    # Mock das chamadas HTTP do AsaasClient
    mock_cus_resp = MagicMock(status_code=200)
    mock_cus_resp.json.return_value = {"id": "cus_12345", "name": "Dra. Marina"}

    mock_pay_resp = MagicMock(status_code=200)
    mock_pay_resp.json.return_value = {
        "id": "pay_98765",
        "value": 149.0,
        "status": "PENDING",
        "invoiceUrl": "https://asaas.com/i/98765",
    }

    mock_qr_resp = MagicMock(status_code=200)
    mock_qr_resp.json.return_value = {
        "payload": "00020126580014br.gov.bcb.pix...6304ABCD",
        "encodedImage": "iVBORw0KGgoAAAANSUhEUgAA...",
    }

    mock_get_empty = MagicMock(status_code=200)
    mock_get_empty.json.return_value = {"data": []}

    with patch("endovision.services.asaas.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.side_effect = [mock_get_empty, mock_qr_resp]
        mock_instance.post.side_effect = [mock_cus_resp, mock_pay_resp]

        res = client.post(
            "/api/v1/billing/create-order",
            json={"plan_type": "lifetime"},
            headers=headers,
        )

        assert res.status_code == 200
        data = res.json()
        assert data["payment_id"] == "pay_98765"
        assert data["plan_type"] == "lifetime"
        assert data["value"] == 149.0
        assert data["pix_copy_paste"] == "00020126580014br.gov.bcb.pix...6304ABCD"
        assert data["pix_qr_code"] == "iVBORw0KGgoAAAANSUhEUgAA..."


def test_payment_status_check_and_pro_upgrade(client, auth_header, db_session):
    headers, user = auth_header

    # Cria um pedido pendente no banco
    order = PaymentOrder(
        user_id=user.id,
        asaas_payment_id="pay_test_confirm",
        plan_type="lifetime",
        billing_type="PIX",
        value=149.0,
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    assert user.is_pro() is False

    # Mock do Asaas retornando CONFIRMED
    mock_status_resp = MagicMock(status_code=200)
    mock_status_resp.json.return_value = {"status": "CONFIRMED"}

    with patch("endovision.services.asaas.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.get.return_value = mock_status_resp

        res = client.get("/api/v1/billing/status/pay_test_confirm")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "CONFIRMED"
        assert data["is_paid"] is True
        assert data["user_plan"] == "pro_lifetime"

    # Confere se no banco o usuário agora é Pro
    db_session.refresh(user)
    assert user.plan == "pro_lifetime"
    assert user.is_pro() is True


def test_webhook_payment_received(client, auth_header, db_session):
    headers, user = auth_header

    order = PaymentOrder(
        user_id=user.id,
        asaas_payment_id="pay_webhook_test",
        plan_type="monthly",
        billing_type="PIX",
        value=29.9,
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    # Dispara webhook
    payload = {
        "event": "PAYMENT_RECEIVED",
        "payment": {
            "id": "pay_webhook_test",
            "value": 29.9,
            "status": "RECEIVED",
        },
    }
    res = client.post("/api/v1/billing/webhook", json=payload)
    assert res.status_code == 200
    assert res.json() == {"received": True}

    # Verifica atualização para Pro Mensal
    db_session.refresh(user)
    assert user.plan == "pro_monthly"
    assert user.is_pro() is True
