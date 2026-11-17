"""Modelos Pydantic de dados para a API do EndoVision."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class RadiographMetrics(BaseModel):
    michelson_contrast: float
    rms_contrast: float
    mean_brightness: float
    min_brightness: float
    max_brightness: float
    std_brightness: float


class EnhanceResponse(BaseModel):
    preset_applied: str
    original_metrics: RadiographMetrics
    enhanced_metrics: RadiographMetrics
    image_base64: str
    processing_time_ms: float
    message: str = "Processamento clínico realizado com sucesso."


class PresetInfo(BaseModel):
    key: str
    name: str
    description: str
    icon: str


class PresetsListResponse(BaseModel):
    presets: list[PresetInfo]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


# --- Schemas de Autenticação ---

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=1)


class ActivateKeyRequest(BaseModel):
    key: str = Field(..., min_length=3, max_length=50)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=10)
    referral_key: Optional[str] = None


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    is_pro: bool


class AuthResponse(BaseModel):
    user: UserProfile
    token: str


# --- Schemas de Cobrança / Asaas ---

class CreateOrderRequest(BaseModel):
    plan_type: str = Field(..., pattern="^(monthly|lifetime)$")
    cpf_cnpj: Optional[str] = None
    phone: Optional[str] = None


class CreateOrderResponse(BaseModel):
    order_id: int
    payment_id: str
    plan_type: str
    value: float
    status: str
    pix_copy_paste: Optional[str] = None
    pix_qr_code: Optional[str] = None
    invoice_url: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    order_id: int
    payment_id: str
    status: str
    is_paid: bool
    user_plan: str
