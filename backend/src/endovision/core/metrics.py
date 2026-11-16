"""Métricas quantitativas de contraste e qualidade de imagem odontológica."""

from __future__ import annotations
import numpy as np


def _ensure_grayscale(image: np.ndarray) -> np.ndarray:
    """Garante que a imagem está em escala de cinza de 1 canal."""
    if image.ndim == 2:
        return image
    if image.ndim == 3:
        if image.shape[2] == 3:
            # Ponderação padrão de luminância médica (ITU-R BT.601)
            r = image[:, :, 0].astype(np.float32)
            g = image[:, :, 1].astype(np.float32)
            b = image[:, :, 2].astype(np.float32)
            gray = 0.299 * r + 0.587 * g + 0.114 * b
            return np.clip(gray, 0, 255).astype(np.uint8)
        if image.shape[2] == 1:
            return image[:, :, 0]
    raise ValueError(f"Dimensão de imagem inválida para radiografia: {image.shape}")


def calculate_michelson_contrast(image: np.ndarray) -> float:
    """Calcula o Contraste de Michelson: (I_max - I_min) / (I_max + I_min).

    Retorna valor entre 0.0 (uniforme) e 1.0 (contraste extremo).
    """
    gray = _ensure_grayscale(image)
    if gray.size == 0:
        return 0.0

    i_min = float(np.min(gray))
    i_max = float(np.max(gray))

    denominator = i_max + i_min
    if denominator == 0.0:
        return 0.0

    return float((i_max - i_min) / denominator)


def calculate_rms_contrast(image: np.ndarray) -> float:
    """Calcula o Contraste RMS (Root-Mean-Square): desvio padrão das intensidades normalizadas.

    Valores típicos: 0.0 (plana) até ~0.5 (alto contraste).
    """
    gray = _ensure_grayscale(image)
    if gray.size == 0:
        return 0.0

    normalized = gray.astype(np.float64) / 255.0
    return float(np.std(normalized))


def calculate_brightness_stats(image: np.ndarray) -> dict[str, float]:
    """Retorna estatísticas detalhadas de distribuição de brilho para diagnóstico."""
    gray = _ensure_grayscale(image)
    if gray.size == 0:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0, "median": 0.0}

    return {
        "min": float(np.min(gray)),
        "max": float(np.max(gray)),
        "mean": float(np.mean(gray)),
        "std": float(np.std(gray)),
        "median": float(np.median(gray)),
    }
