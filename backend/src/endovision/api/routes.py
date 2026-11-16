"""Rotas da API do EndoVision."""

from __future__ import annotations
import time
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from endovision.api.schemas import (
    EnhanceResponse,
    PresetInfo,
    PresetsListResponse,
    RadiographMetrics,
)
from endovision.core.pipeline import (
    PRESET_METADATA,
    DentalPreset,
    decode_image_bytes,
    encode_image_to_base64,
    process_radiograph,
)

router = APIRouter(prefix="/api/v1", tags=["EndoVision"])


@router.get("/presets", response_model=PresetsListResponse)
async def list_presets() -> PresetsListResponse:
    """Lista todos os presets clínicos disponíveis com descrição e ícone."""
    items = []
    for preset_enum, meta in PRESET_METADATA.items():
        items.append(
            PresetInfo(
                key=preset_enum.value,
                name=meta["name"],
                description=meta["description"],
                icon=meta["icon"],
            )
        )
    return PresetsListResponse(presets=items)


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_radiograph_endpoint(
    file: UploadFile = File(...),
    preset: str = Form("apical_enhancement"),
    gamma: Optional[float] = Form(None),
    clahe_clip: Optional[float] = Form(None),
    unsharp_strength: Optional[float] = Form(None),
    invert: Optional[bool] = Form(None),
    normalize_range: Optional[bool] = Form(True),
) -> EnhanceResponse:
    """Recebe imagem radiográfica e aplica o pipeline de aprimoramento clínico selecionado."""
    start_time = time.perf_counter()

    try:
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo enviado está vazio.",
            )

        image_array = decode_image_bytes(raw_bytes)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo de imagem inválido ou corrompido: {err}",
        ) from err

    # Validar ou instanciar Preset
    try:
        selected_preset = DentalPreset(preset)
    except ValueError:
        selected_preset = DentalPreset.CUSTOM

    custom_params = {}
    if gamma is not None:
        custom_params["gamma"] = gamma
    if clahe_clip is not None:
        custom_params["clahe_clip"] = clahe_clip
    if unsharp_strength is not None:
        custom_params["unsharp_strength"] = unsharp_strength
    if invert is not None:
        custom_params["invert"] = invert
    if normalize_range is not None:
        custom_params["normalize_range"] = normalize_range

    try:
        enhanced_arr, orig_metrics, enh_metrics = process_radiograph(
            image=image_array,
            preset=selected_preset,
            custom_params=custom_params if custom_params else None,
        )
        base64_str = encode_image_to_base64(enhanced_arr)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o processamento da radiografia: {err}",
        ) from err

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    return EnhanceResponse(
        preset_applied=selected_preset.value,
        original_metrics=RadiographMetrics(**orig_metrics),
        enhanced_metrics=RadiographMetrics(**enh_metrics),
        image_base64=base64_str,
        processing_time_ms=elapsed_ms,
    )
