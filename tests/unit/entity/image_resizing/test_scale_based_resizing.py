import numpy as np
import pytest
from PIL import Image

from entity.image_resizing.scale_based_resizing import (
    scale_bar,
    resize_image_based_on_scale,
    scale_based_resizing,
    scale_PIL_adapter,
)


def test_scale_bar_raises_on_empty_image():
    template = np.zeros((5, 5, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="Empty image"):
        scale_bar(np.array([]), template)


def test_resize_image_based_on_scale_scales_image():
    image = np.zeros((10, 20, 3), dtype=np.uint8)

    resized = resize_image_based_on_scale(image, scale_factor=2.0, target_scale=1.0)

    assert resized.shape[:2] == (20, 40)


def test_resize_image_based_on_scale_rejects_none_scale():
    image = np.zeros((5, 5, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="Scale factor is None"):
        resize_image_based_on_scale(image, scale_factor=None)  # type: ignore[arg-type]


def test_scale_based_resizing_uses_detected_scale(monkeypatch):
    image = np.zeros((6, 8, 3), dtype=np.uint8)
    template = np.zeros((2, 2, 3), dtype=np.uint8)

    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.scale_bar", lambda *args, **kwargs: 1.5)
    monkeypatch.setattr(
        "entity.image_resizing.scale_based_resizing.resize_image_based_on_scale",
        lambda image, scale_factor, target_scale: np.ones((3, 4, 3), dtype=np.uint8) * 7,
    )

    out = scale_based_resizing(image, template, bar_length=500, target_scale=1.0)

    assert out.shape == (3, 4, 3)
    assert int(out[0, 0, 0]) == 7


def test_scale_based_resizing_raises_when_scale_bar_missing(monkeypatch):
    image = np.zeros((6, 8, 3), dtype=np.uint8)
    template = np.zeros((2, 2, 3), dtype=np.uint8)
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.scale_bar", lambda *args, **kwargs: None)

    with pytest.raises(ValueError, match="could not be detected"):
        scale_based_resizing(image, template, bar_length=500, target_scale=1.0)


def test_scale_bar_returns_scale_factor_with_mocked_cv(monkeypatch):
    fake_contour = np.array([[[0, 0]], [[5, 0]], [[5, 1]], [[0, 1]]], dtype=np.int32)

    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.cvtColor", lambda img, code: img[:, :, 0] if img.ndim == 3 else img)
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.threshold", lambda img, t, m, mode: (0, img))
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.matchTemplate", lambda img, template, mode: np.array([[0.9]]))
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.bitwise_not", lambda img: img)
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.findContours", lambda img, mode, method: ([fake_contour], None))
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.contourArea", lambda contour: 10.0)
    monkeypatch.setattr("entity.image_resizing.scale_based_resizing.cv2.boundingRect", lambda contour: (0, 0, 5, 1))

    image = np.ones((10, 10, 3), dtype=np.uint8)
    template = np.ones((3, 3, 3), dtype=np.uint8)
    factor = scale_bar(image, template, bar_length=500)

    assert factor == 100.0


def test_scale_pil_adapter_returns_pil_image(monkeypatch):
    monkeypatch.setattr(
        "entity.image_resizing.scale_based_resizing.scale_based_resizing",
        lambda image, template, bar_length, target_scale: np.zeros((4, 4, 3), dtype=np.uint8),
    )

    input_image = Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8))
    template = Image.fromarray(np.zeros((1, 1, 3), dtype=np.uint8))

    out = scale_PIL_adapter(input_image, template, bar_length=500, target_scale=1)

    assert isinstance(out, Image.Image)
    assert out.size == (4, 4)
