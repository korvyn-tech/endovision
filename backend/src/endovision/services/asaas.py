"""Serviço de integração com a API v3 do Asaas para pagamentos via Pix e assinaturas."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import httpx
from sqlalchemy.orm import Session

from endovision.db.models import PaymentOrder, User

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")
ASAAS_ENVIRONMENT = os.getenv("ASAAS_ENVIRONMENT", "production").lower()

if ASAAS_ENVIRONMENT == "sandbox":
    ASAAS_BASE_URL = "https://sandbox.asaas.com/v3"
else:
    ASAAS_BASE_URL = "https://api.asaas.com/v3"


class AsaasClient:
    """Cliente HTTP para comunicação com a API do Asaas."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or ASAAS_API_KEY
        self.base_url = (base_url or ASAAS_BASE_URL).rstrip("/")
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "EndoVision-Korvyn/1.0",
        }

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self.headers, timeout=20.0)

    def get_or_create_customer(self, db: Session, user: User) -> str:
        """Obtém ou cadastra o cliente no Asaas. Retorna o ID do cliente (cus_...)."""
        if user.asaas_customer_id:
            return user.asaas_customer_id

        with self._client() as client:
            # Tenta buscar por e-mail primeiro
            resp = client.get(f"{self.base_url}/customers", params={"email": user.email})
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    cus_id = data[0]["id"]
                    user.asaas_customer_id = cus_id
                    db.commit()
                    return cus_id

            # Se não existir, cadastra novo cliente
            payload = {
                "name": user.name or "Doutor(a)",
                "email": user.email,
                "externalReference": f"user_{user.id}",
                "notificationDisabled": False,
            }
            create_resp = client.post(f"{self.base_url}/customers", json=payload)
            create_resp.raise_for_status()
            cus_data = create_resp.json()
            cus_id = cus_data["id"]
            user.asaas_customer_id = cus_id
            db.commit()
            return cus_id

    def create_order(self, db: Session, user: User, plan_type: str) -> Dict[str, Any]:
        """Cria cobrança Pix (vitalícia ou assinatura mensal) e retorna dados do Pix."""
        customer_id = self.get_or_create_customer(db, user)

        due_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")

        with self._client() as client:
            if plan_type == "monthly":
                value = 29.90
                # Cria assinatura mensal no Asaas
                sub_payload = {
                    "customer": customer_id,
                    "billingType": "PIX",
                    "value": value,
                    "nextDueDate": due_date,
                    "cycle": "MONTHLY",
                    "description": "EndoVision Pro - Assinatura Mensal (Korvyn)",
                    "externalReference": f"user_{user.id}_monthly",
                }
                sub_resp = client.post(f"{self.base_url}/subscriptions", json=sub_payload)
                sub_resp.raise_for_status()
                sub_data = sub_resp.json()
                sub_id = sub_data["id"]

                # Busca a primeira cobrança gerada pela assinatura para obter o QR Code Pix
                payments_resp = client.get(f"{self.base_url}/subscriptions/{sub_id}/payments")
                payments_resp.raise_for_status()
                payments_data = payments_resp.json().get("data", [])
                if not payments_data:
                    raise RuntimeError("Falha ao recuperar primeira cobrança da assinatura.")

                payment_data = payments_data[0]
                payment_id = payment_data["id"]
                invoice_url = payment_data.get("invoiceUrl")

            elif plan_type == "lifetime":
                value = 149.00
                pay_payload = {
                    "customer": customer_id,
                    "billingType": "PIX",
                    "value": value,
                    "dueDate": due_date,
                    "description": "EndoVision Pro - Acesso Vitalício (Korvyn)",
                    "externalReference": f"user_{user.id}_lifetime",
                }
                pay_resp = client.post(f"{self.base_url}/payments", json=pay_payload)
                pay_resp.raise_for_status()
                payment_data = pay_resp.json()
                payment_id = payment_data["id"]
                invoice_url = payment_data.get("invoiceUrl")
            else:
                raise ValueError(f"Tipo de plano inválido: {plan_type}")

            # Busca o QR Code e código Copia e Cola do Pix
            qr_resp = client.get(f"{self.base_url}/payments/{payment_id}/pixQrCode")
            qr_resp.raise_for_status()
            qr_data = qr_resp.json()

            pix_payload = qr_data.get("payload")
            encoded_image = qr_data.get("encodedImage")

            # Salva o pedido no banco de dados
            order = PaymentOrder(
                user_id=user.id,
                asaas_payment_id=payment_id,
                plan_type=plan_type,
                billing_type="PIX",
                value=value,
                status="PENDING",
                pix_copy_paste=pix_payload,
                pix_qr_code=encoded_image,
                invoice_url=invoice_url,
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            return {
                "order_id": order.id,
                "payment_id": payment_id,
                "plan_type": plan_type,
                "value": value,
                "status": "PENDING",
                "pix_copy_paste": pix_payload,
                "pix_qr_code": encoded_image,
                "invoice_url": invoice_url,
            }

    def check_payment_status(self, db: Session, asaas_payment_id: str) -> Dict[str, Any]:
        """Consulta status do pagamento no Asaas. Se aprovado, ativa Pro no usuário."""
        order = db.query(PaymentOrder).filter(PaymentOrder.asaas_payment_id == asaas_payment_id).first()
        if not order:
            raise ValueError("Pedido não encontrado.")

        user = db.query(User).filter(User.id == order.user_id).first()

        with self._client() as client:
            resp = client.get(f"{self.base_url}/payments/{asaas_payment_id}")
            resp.raise_for_status()
            data = resp.json()
            asaas_status = data.get("status", "PENDING")

            # Status de sucesso no Asaas: RECEIVED, CONFIRMED, RECEIVED_IN_CASH
            paid = asaas_status in ("RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH")
            if paid:
                order.status = "CONFIRMED"
                if user:
                    if order.plan_type == "lifetime":
                        user.plan = "pro_lifetime"
                    else:
                        user.plan = "pro_monthly"
                db.commit()
            elif asaas_status in ("OVERDUE", "REFUNDED"):
                order.status = asaas_status
                db.commit()

            return {
                "order_id": order.id,
                "payment_id": asaas_payment_id,
                "status": order.status,
                "is_paid": paid,
                "user_plan": user.plan if user else "free",
            }
