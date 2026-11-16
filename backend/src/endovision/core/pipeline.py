"""Orquestrador de pipelines e presets clínicos de radiografia periapical."""

from __future__ import annotations
import base64
import io
from enum import Enum
from typing import Any
import cv2
import numpy as np
from PIL import Image

from endovision.core.filters import (
    adjust_gamma,
    apply_clahe,
    apply_unsharp_mask,
    invert_radiograph,
    normalize_dynamic_range,
    to_dental_grayscale,
)
from endovision.core.metrics import (
    calculate_brightness_stats,
    calculate_michelson_contrast,
    calculate_rms_contrast,
)


class DentalPreset(str, Enum):
    APICAL_ENHANCEMENT = "apical_enhancement"
    CALCIFIED_CANALS = "calcified_canals"
    CONTRAST_RECOVERY = "contrast_recovery"
    NEGATIVE_INVERT = "negative_invert"
    CUSTOM = "custom"


PRESET_METADATA = {
    DentalPreset.APICAL_ENHANCEMENT: {
        "name": "Realce de Ápice e Forame",
        "description": "Acentua o terço apical e constrição foraminal para odontometria segura.",
        "icon": "crosshair",
    },
    DentalPreset.CALCIFIED_CANALS: {
        "name": "Canais Atresiados e Calcificados",
        "description": "Realça micro-linhas anatômicas de alta densidade e condutos estreitos.",
        "icon": "activity",
    },
    DentalPreset.CONTRAST_RECOVERY: {
        "name": "Recuperar Exposição (CLAHE)",
        "description": "Equilíbrio tonal ideal para radiografias lavadas ou com flash de negatoscópio.",
        "icon": "sun",
    },
    DentalPreset.NEGATIVE_INVERT: {
        "name": "Inversão Diagnóstica (Negativo)",
        "description": "Inverte tons para evidenciar fraturas radiculares e lesões periapicais.",
        "icon": "moon",
    },
    DentalPreset.CUSTOM: {
        "name": "Ajuste Personalizado",
        "description": "Controle manual fino de gama, contraste, nitidez e inversão.",
        "icon": "sliders",
    },
}


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decodifica stream de bytes de imagem (PNG, JPEG, WebP, TIFF) em matriz NumPy 2D dental."""
    if not image_bytes or len(image_bytes) < 8:
        raise ValueError("Não foi possível decodificar os bytes da imagem: dados vazios.")

    # Tentativa 1 via OpenCV
    np_buf = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_buf, cv2.IMREAD_UNCHANGED)

    # Tentativa 2 via Pillow (fallback para formatos médicos e TIFFs específicos)
    if img is None:
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            img = np.array(pil_img)
        except Exception as err:
            raise ValueError(f"Não foi possível decodificar os bytes da imagem: {err}") from err

    if img is None or img.size == 0:
        raise ValueError("Não foi possível decodificar a imagem informada.")

    return to_dental_grayscale(img)


def encode_image_to_base64(image: np.ndarray, format_ext: str = ".png") -> str:
    """Codifica matriz de imagem em string base64 data URI."""
    success, buffer = cv2.imencode(format_ext, image)
    if not success:
        raise RuntimeError("Falha ao codificar imagem processada para formato web.")
    b64_data = base64.b64encode(buffer).decode("utf-8")
    mime = "image/png" if format_ext.endswith("png") else "image/jpeg"
    return f"data:{mime};base64,{b64_data}"


def _collect_metrics(image: np.ndarray) -> dict[str, float]:
    """Coleta pacote de métricas clínicas de contraste e luminosidade."""
    stats = calculate_brightness_stats(image)
    return {
        "michelson_contrast": round(calculate_michelson_contrast(image), 4),
        "rms_contrast": round(calculate_rms_contrast(image), 4),
        "mean_brightness": round(stats["mean"], 2),
        "min_brightness": round(stats["min"], 2),
        "max_brightness": round(stats["max"], 2),
        "std_brightness": round(stats["std"], 2),
    }


def process_radiograph(
    image: np.ndarray,
    preset: DentalPreset | str = DentalPreset.APICAL_ENHANCEMENT,
    custom_params: dict[str, Any] | None = None,
) -> tuple[np.ndarray, dict[str, float], dict[str, float]]:
    """Aplica o pipeline clínico de processamento e retorna imagem melhorada e métricas.

    Retorna: (imagem_aprimorada, metricas_originais, metricas_aprimoradas)
    """
    gray = to_dental_grayscale(image)
    original_metrics = _collect_metrics(gray)

    if isinstance(preset, str):
        preset = DentalPreset(preset)

    enhanced = gray.copy()

    if preset == DentalPreset.APICAL_ENHANCEMENT:
        enhanced = normalize_dynamic_range(enhanced, low_percentile=1.0, high_percentile=99.0)
        enhanced = apply_clahe(enhanced, clip_limit=3.5, tile_grid_size=(8, 8))
        enhanced = adjust_gamma(enhanced, gamma=1.2)
        enhanced = apply_unsharp_mask(enhanced, sigma=1.0, strength=1.4)

    elif preset == DentalPreset.CALCIFIED_CANALS:
        enhanced = normalize_dynamic_range(enhanced, low_percentile=0.5, high_percentile=99.5)
        enhanced = apply_clahe(enhanced, clip_limit=4.5, tile_grid_size=(6, 6))
        enhanced = apply_unsharp_mask(enhanced, sigma=0.8, strength=1.8)

    elif preset == DentalPreset.CONTRAST_RECOVERY:
        enhanced = normalize_dynamic_range(enhanced, low_percentile=2.0, high_percentile=98.0)
        enhanced = apply_clahe(enhanced, clip_limit=2.5, tile_grid_size=(8, 8))
        enhanced = adjust_gamma(enhanced, gamma=1.15)

    elif preset == DentalPreset.NEGATIVE_INVERT:
        enhanced = invert_radiograph(enhanced)
        enhanced = apply_clahe(enhanced, clip_limit=3.0, tile_grid_size=(8, 8))
        enhanced = apply_unsharp_mask(enhanced, sigma=1.0, strength=1.2)

    elif preset == DentalPreset.CUSTOM:
        params = custom_params or {}
        if params.get("normalize_range", True):
            enhanced = normalize_dynamic_range(enhanced)
        if params.get("invert", False):
            enhanced = invert_radiograph(enhanced)

        clahe_clip = float(params.get("clahe_clip", 0.0))
        if clahe_clip > 0:
            enhanced = apply_clahe(enhanced, clip_limit=clahe_clip)

        gamma = float(params.get("gamma", 1.0))
        if gamma != 1.0 and gamma > 0:
            enhanced = adjust_gamma(enhanced, gamma=gamma)

        unsharp = float(params.get("unsharp_strength", 0.0))
        if unsharp > 0:
            enhanced = apply_unsharp_mask(enhanced, strength=unsharp)

    enhanced_metrics = _collect_metrics(enhanced)
    return enhanced, original_metrics, enhanced_metrics
