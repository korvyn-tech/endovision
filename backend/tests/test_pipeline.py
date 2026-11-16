import io
import cv2
import numpy as np
import pytest
from PIL import Image
from endovision.core.pipeline import (
    DentalPreset,
    decode_image_bytes,
    encode_image_to_base64,
    process_radiograph,
)


def create_sample_png_bytes(shape=(150, 150), gray_range=(160, 210)) -> bytes:
    """Gera bytes PNG de uma imagem simulando radiografia periapical com superexposição."""
    arr = np.random.randint(gray_range[0], gray_range[1], size=shape, dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def test_decode_image_bytes():
    """Valida decodificação de stream de bytes de imagem PNG e JPEG."""
    raw_bytes = create_sample_png_bytes()
    img = decode_image_bytes(raw_bytes)
    assert isinstance(img, np.ndarray)
    assert img.shape == (150, 150)


def test_decode_invalid_bytes_raises_error():
    """Bytes corrompidos ou aleatórios devem levantar ValueError explicativo."""
    with pytest.raises(ValueError, match="Não foi possível decodificar"):
        decode_image_bytes(b"dados_invalidos_nao_imagem")


def test_process_radiograph_apical_preset():
    """Preset 'apical_enhancement' deve aumentar significativamente contraste e métricas."""
    raw_bytes = create_sample_png_bytes()
    img = decode_image_bytes(raw_bytes)

    enhanced, orig_metrics, enh_metrics = process_radiograph(
        img, preset=DentalPreset.APICAL_ENHANCEMENT
    )

    assert enhanced.shape == img.shape
    assert enh_metrics["rms_contrast"] > orig_metrics["rms_contrast"]
    assert enh_metrics["michelson_contrast"] >= orig_metrics["michelson_contrast"]


def test_process_radiograph_negative_invert_preset():
    """Preset 'negative_invert' inverte os níveis e realça canais."""
    raw_bytes = create_sample_png_bytes()
    img = decode_image_bytes(raw_bytes)

    enhanced, orig_metrics, enh_metrics = process_radiograph(
        img, preset=DentalPreset.NEGATIVE_INVERT
    )
    # Na inversão de tons claros (média ~185), a média deve cair para ~70
    assert enh_metrics["mean_brightness"] < orig_metrics["mean_brightness"]


def test_process_radiograph_custom_params():
    """Permite passar parâmetros manuais para ajustes finos em consultório."""
    img = np.full((100, 100), 180, dtype=np.uint8)
    enhanced, _, _ = process_radiograph(
        img,
        preset=DentalPreset.CUSTOM,
        custom_params={"gamma": 2.0, "clahe_clip": 1.0, "unsharp_strength": 0.0, "invert": False},
    )
    # Gama 2.0 escurece
    assert np.all(enhanced < 180)


def test_encode_image_to_base64():
    """Valida serialização em base64 com header data:image/png;base64."""
    img = np.zeros((20, 20), dtype=np.uint8)
    b64_str = encode_image_to_base64(img)
    assert b64_str.startswith("data:image/png;base64,")
    assert len(b64_str) > 50
