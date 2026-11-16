import numpy as np
import pytest
from endovision.core.metrics import (
    calculate_brightness_stats,
    calculate_michelson_contrast,
    calculate_rms_contrast,
)


def test_michelson_contrast_flat_image():
    """Uma imagem uniforme (sem variação de tom) tem contraste Michelson zero."""
    flat_gray = np.full((100, 100), 128, dtype=np.uint8)
    assert calculate_michelson_contrast(flat_gray) == pytest.approx(0.0, abs=1e-5)

    flat_black = np.zeros((100, 100), dtype=np.uint8)
    assert calculate_michelson_contrast(flat_black) == pytest.approx(0.0, abs=1e-5)


def test_michelson_contrast_extreme_black_and_white():
    """Uma imagem com pretos e brancos puros atinge contraste Michelson máximo (1.0)."""
    checker = np.zeros((100, 100), dtype=np.uint8)
    checker[::2, ::2] = 255
    checker[1::2, 1::2] = 255
    assert calculate_michelson_contrast(checker) == pytest.approx(1.0, abs=1e-5)


def test_michelson_contrast_washed_out_radiograph():
    """Radiografia lavada (faixa dinâmica comprimida, ex: 180 a 220) tem baixo contraste."""
    washed_out = np.random.randint(180, 221, size=(200, 200), dtype=np.uint8)
    c = calculate_michelson_contrast(washed_out)
    assert 0.0 < c < 0.2


def test_rms_contrast_flat_and_pattern():
    """O contraste RMS mede o desvio padrão das intensidades normalizadas."""
    flat = np.full((50, 50), 100, dtype=np.uint8)
    assert calculate_rms_contrast(flat) == pytest.approx(0.0, abs=1e-5)

    high_contrast = np.zeros((50, 50), dtype=np.uint8)
    high_contrast[:25, :] = 255
    rms = calculate_rms_contrast(high_contrast)
    assert rms > 0.4


def test_brightness_stats():
    """Valida extração de estatísticas de brilho e histograma."""
    img = np.array([[50, 100], [150, 200]], dtype=np.uint8)
    stats = calculate_brightness_stats(img)
    assert stats["min"] == 50.0
    assert stats["max"] == 200.0
    assert stats["mean"] == pytest.approx(125.0, abs=1e-3)
    assert stats["std"] > 0


def test_metrics_handles_rgb_conversion_automatically():
    """Se uma imagem de 3 canais (RGB) for passada, as métricas devem calcular na escala de cinza."""
    rgb = np.full((50, 50, 3), 128, dtype=np.uint8)
    assert calculate_michelson_contrast(rgb) == pytest.approx(0.0, abs=1e-5)
