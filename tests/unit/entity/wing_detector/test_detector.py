import numpy as np
import pytest

from entity.wing_detector.detector import WingDetector


def _contour(area_scale):
    return np.array([[[0, 0]], [[area_scale, 0]], [[area_scale, area_scale]], [[0, area_scale]]], dtype=np.int32)


def test_detect_raises_when_no_contour(monkeypatch):
    monkeypatch.setattr("entity.wing_detector.detector.find_contour", lambda image: None)

    detector = WingDetector()

    with pytest.raises(ValueError, match="No contour found"):
        detector.detect(np.zeros((10, 10), dtype=np.uint8), (0, 0), (1, 1))


def test_detect_returns_larger_split_contour(monkeypatch):
    contour = _contour(10)
    smaller = _contour(3)
    larger = _contour(8)

    monkeypatch.setattr("entity.wing_detector.detector.find_contour", lambda image: contour)
    monkeypatch.setattr("entity.wing_detector.detector.crop_contour", lambda c, p1, p2: [smaller, larger])

    detector = WingDetector()
    result = detector.detect(np.zeros((20, 20), dtype=np.uint8), (0, 0), (1, 1))

    assert np.array_equal(result, larger)
