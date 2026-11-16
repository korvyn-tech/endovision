"""Filtros especializados de processamento digital para radiografias odontológicas."""

from __future__ import annotations
import cv2
import numpy as np


def to_dental_grayscale(image: np.ndarray, is_bgr: bool = False) -> np.ndarray:
    """Converte a imagem de entrada para escala de cinza médica (8-bit monocanal).

    Por padrão, assume ordem RGB (padrão de uploads web e bibliotecas modernas).
    """
    if image is None or image.size == 0:
        raise ValueError("Imagem vazia ou inválida.")

    # Se for de 16 bits (comum em sensores digitais de radiografia), converte para 8 bits
    if image.dtype == np.uint16:
        image = (image / 256.0).astype(np.uint8)

    if image.ndim == 2:
        return image.astype(np.uint8)

    if image.ndim == 3:
        if image.shape[2] == 4:
            conversion = cv2.COLOR_BGRA2GRAY if is_bgr else cv2.COLOR_RGBA2GRAY
            return cv2.cvtColor(image, conversion)
        if image.shape[2] == 3:
            conversion = cv2.COLOR_BGR2GRAY if is_bgr else cv2.COLOR_RGB2GRAY
            return cv2.cvtColor(image, conversion)
        if image.shape[2] == 1:
            return image[:, :, 0].astype(np.uint8)

    raise ValueError(f"Formato de imagem incompatível: {image.shape}")


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 3.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).

    Ideal para revelar canais radiculares e trabeculado ósseo sem amplificar ruído excessivo.
    """
    gray = to_dental_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tile_grid_size)
    return clahe.apply(gray)


def adjust_gamma(image: np.ndarray, gamma: float) -> np.ndarray:
    """Ajusta a curva de gama via Look-Up Table (LUT).

    - gamma > 1.0: escurece tons médios/claros (recupera radiografias 'lavadas' ou superexpostas)
    - gamma < 1.0: eleva luminosidade de áreas subexpostas
    """
    if gamma <= 0:
        raise ValueError("O valor de gama deve ser estritamente positivo.")

    gray = to_dental_grayscale(image)
    inv_gamma = float(gamma)
    table = np.array(
        [((i / 255.0) ** inv_gamma) * 255 for i in range(256)], dtype=np.uint8
    )
    return cv2.LUT(gray, table)


def apply_unsharp_mask(
    image: np.ndarray,
    sigma: float = 1.0,
    strength: float = 1.5,
) -> np.ndarray:
    """Acentua bordas e microestruturas (máscara de desfoque/unsharp mask).

    Realça a linha do ligamento periodontal, ápice e fraturas radiculares.
    """
    gray = to_dental_grayscale(image).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=float(sigma))
    sharpened = gray + float(strength) * (gray - blurred)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def invert_radiograph(image: np.ndarray) -> np.ndarray:
    """Inverte os níveis de cinza (negativo digital).

    Facilita a identificação de lesões osteolíticas periapicais e canais acessórios.
    """
    gray = to_dental_grayscale(image)
    return cv2.bitwise_not(gray)


def normalize_dynamic_range(
    image: np.ndarray,
    low_percentile: float = 1.0,
    high_percentile: float = 99.0,
) -> np.ndarray:
    """Estica a faixa dinâmica usando percentis robustos para preencher toda a escala tonal 0..255."""
    gray = to_dental_grayscale(image)
    p_low, p_high = float(np.percentile(gray, low_percentile)), float(
        np.percentile(gray, high_percentile)
    )

    if p_high <= p_low:
        p_low, p_high = float(np.min(gray)), float(np.max(gray))

    if p_high <= p_low:
        return gray

    clipped = np.clip(gray, p_low, p_high)
    stretched = ((clipped - p_low) / (p_high - p_low)) * 255.0
    return np.clip(stretched, 0, 255).astype(np.uint8)
