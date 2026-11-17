"""Modelos de banco de dados para Usuários e Pedidos de Pagamento."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from endovision.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Modelo de usuário do EndoVision."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(50), default="free", nullable=False)  # free, pro_monthly, pro_lifetime
    asaas_customer_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")

    def is_pro(self) -> bool:
        """Verifica se o usuário possui plano Pro ativo."""
        return self.plan in ("pro_monthly", "pro_lifetime")


class PaymentOrder(Base):
    """Modelo de pedido e cobrança via Asaas."""

    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asaas_payment_id = Column(String(100), unique=True, index=True, nullable=False)
    plan_type = Column(String(50), nullable=False)  # monthly, lifetime
    billing_type = Column(String(20), default="PIX", nullable=False)  # PIX, CREDIT_CARD
    value = Column(Float, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, RECEIVED, CONFIRMED, OVERDUE
    pix_copy_paste = Column(Text, nullable=True)
    pix_qr_code = Column(Text, nullable=True)  # Base64 da imagem
    invoice_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="orders")
