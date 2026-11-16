"""Modelos Pydantic de dados para a API do EndoVision."""

from __future__ import annotations
from typing import Any
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
