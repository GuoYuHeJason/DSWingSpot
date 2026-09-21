import numpy as np

from entity.spot_detector.detector import SpotDetector, AlgSpotDetector


def test_to_bool_conversions():
    assert SpotDetector._to_bool(True) is True
    assert SpotDetector._to_bool(" yes ") is True
    assert SpotDetector._to_bool("0") is False
    assert SpotDetector._to_bool("unknown") is False


def test_alg_spot_detector_passes_parameters(monkeypatch):
    captured = {}

    def fake_find_spot_contour(image, wing_contour, **kwargs):
        captured.update(kwargs)
        return np.array([[[1, 1]], [[2, 2]], [[3, 1]]], dtype=np.int32)

    monkeypatch.setattr("entity.spot_detector.detector.find_spot_contour", fake_find_spot_contour)

    params = {
        "bin_thresh": 100,
        "min_black_pixels": 3,
        "min_black_width": 2,
        "median_blur_ksize": 5,
        "close_kernel_hori": 7,
        "close_kernel_vert": 7,
        "open_kernel_hori": 5,
        "open_kernel_vert": 3,
        "adjust_bin_thresh": "true",
        "min_spot_area": 10,
        "wing_height_percent": 0.5,
        "left_most_point_adjustment": 2,
        "centroid_adjustment": 0,
        "adjust_rate": 0.9,
    }
    detector = AlgSpotDetector(params)

    result = detector.detect(np.zeros((10, 10), dtype=np.uint8), np.array([[[0, 0]]], dtype=np.int32))

    assert result is not None
    assert captured["adjust_bin_thresh"] is True
    assert captured["contour_area_threshold"] == 10
    assert captured["cut_right_half"] is True
