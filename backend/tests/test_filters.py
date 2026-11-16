import numpy as np
import pytest
from endovision.core.filters import (
    adjust_gamma,
    apply_clahe,
    apply_unsharp_mask,
    invert_radiograph,
    normalize_dynamic_range,
    to_dental_grayscale,
)
from endovision.core.metrics import calculate_rms_contrast


def test_to_dental_grayscale():
    """Converte corretamente imagens RGB e mantém imagens 2D."""
    rgb = np.zeros((100, 100, 3), dtype=np.uint8)
    rgb[:, :, 0] = 50   # R
    rgb[:, :, 1] = 100  # G
    rgb[:, :, 2] = 150  # B
    gray = to_dental_grayscale(rgb)
    assert gray.ndim == 2
    assert gray.shape == (100, 100)
    # 0.299*50 + 0.587*100 + 0.114*150 = 90.75 -> 91
    assert 85 <= gray[0, 0] <= 95

    already_gray = np.full((50, 50), 200, dtype=np.uint8)
    assert np.array_equal(to_dental_grayscale(already_gray), already_gray)


def test_apply_clahe_enhances_contrast():
    """CLAHE aumenta o contraste RMS em uma radiografia com baixo contraste simulada."""
    low_contrast = np.random.randint(100, 140, size=(128, 128), dtype=np.uint8)
    initial_rms = calculate_rms_contrast(low_contrast)

    enhanced = apply_clahe(low_contrast, clip_limit=3.0, tile_grid_size=(8, 8))
    enhanced_rms = calculate_rms_contrast(enhanced)

    assert enhanced_rms > initial_rms
    assert enhanced.shape == low_contrast.shape
    assert enhanced.dtype == np.uint8


def test_adjust_gamma():
    """Ajuste de gama altera a curva tonal sem violar limites de 8 bits [0, 255]."""
    img = np.full((50, 50), 128, dtype=np.uint8)

    # Gama > 1 escurece tons médios para resgatar superexposição
    darker = adjust_gamma(img, gamma=1.8)
    assert np.all(darker < 128)

    # Gama < 1 clareia tons médios para resgatar subexposição
    lighter = adjust_gamma(img, gamma=0.5)
    assert np.all(lighter > 128)

    assert darker.dtype == np.uint8
    assert lighter.dtype == np.uint8


def test_apply_unsharp_mask():
    """Máscara de nitidez aumenta a variância de bordas mantendo dimensões."""
    step_edge = np.zeros((100, 100), dtype=np.uint8)
    step_edge[:, 50:] = 180

    sharpened = apply_unsharp_mask(step_edge, sigma=1.0, strength=2.0)
    assert sharpened.shape == step_edge.shape
    assert sharpened.dtype == np.uint8
    assert sharpened[50, 49] <= step_edge[50, 49]
    assert sharpened[50, 51] >= step_edge[50, 51]


def test_invert_radiograph():
    """Inversão digital de radiografia (negativo <-> positivo)."""
    img = np.array([[0, 55], [200, 255]], dtype=np.uint8)
    inverted = invert_radiograph(img)
    expected = np.array([[255, 200], [55, 0]], dtype=np.uint8)
    assert np.array_equal(inverted, expected)


def test_normalize_dynamic_range():
    """Normaliza e estica os percentis para cobrir 0..255."""
    gradient = np.linspace(60, 180, 10000, dtype=np.uint8).reshape((100, 100))
    stretched = normalize_dynamic_range(gradient, low_percentile=1.0, high_percentile=99.0)
    assert stretched.min() == 0
    assert stretched.max() == 255
