"""Rotas de faturamento e integração com Asaas (criação de cobrança Pix, polling e webhook)."""

from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from endovision.api.routers.auth import require_user
from endovision.api.schemas import CreateOrderRequest, CreateOrderResponse, PaymentStatusResponse
from endovision.db.database import get_db
from endovision.db.models import PaymentOrder, User
from endovision.services.asaas import AsaasClient

logger = logging.getLogger("endovision.billing")
router = APIRouter(prefix="/api/v1/billing", tags=["Cobrança e Asaas"])
asaas_client = AsaasClient()


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    req: CreateOrderRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Gera uma cobrança Pix no Asaas (Assinatura mensal ou Vitalício)."""
    try:
        order_data = asaas_client.create_order(db, user, req.plan_type)
        return CreateOrderResponse(**order_data)
    except Exception as exc:
        logger.exception("Erro ao gerar cobrança no Asaas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Não foi possível gerar a cobrança no gateway Asaas: {str(exc)}",
        )


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """Consulta o status da cobrança no Asaas e atualiza o usuário se aprovado."""
    try:
        status_data = asaas_client.check_payment_status(db, payment_id)
        return PaymentStatusResponse(**status_data)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        logger.exception("Erro ao verificar status do pagamento: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao consultar Asaas: {str(exc)}",
        )


@router.post("/webhook")
async def asaas_webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe webhooks do Asaas notificando pagamento confirmado."""
    try:
        payload = await request.json()
        event = payload.get("event")
        payment_info = payload.get("payment", {})
        payment_id = payment_info.get("id")

        logger.info("Recebido webhook Asaas: evento=%s payment_id=%s", event, payment_id)

        if event in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED") and payment_id:
            order = db.query(PaymentOrder).filter(PaymentOrder.asaas_payment_id == payment_id).first()
            if order:
                order.status = "CONFIRMED"
                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    if order.plan_type == "lifetime":
                        user.plan = "pro_lifetime"
                    else:
                        user.plan = "pro_monthly"
                db.commit()
                logger.info("Plano do usuário atualizado com sucesso via webhook.")

        return {"received": True}
    except Exception as exc:
        logger.exception("Erro no processamento de webhook: %s", exc)
        return {"received": False, "error": str(exc)}
