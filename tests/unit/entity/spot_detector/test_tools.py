import numpy as np
import pytest

from entity.spot_detector.tools import (
    image_preprocessing,
    get_morphological_kernels,
    get_width_of_black_region,
    find_spot_contour,
)


def test_image_preprocessing_returns_grayscale():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    image[:, :, 1] = 120

    gray = image_preprocessing(image, median_kernel_size=3)

    assert gray.ndim == 2
    assert gray.shape == (20, 20)


def test_get_morphological_kernels_invalid_operation_raises():
    with pytest.raises(ValueError, match="Invalid operation"):
        get_morphological_kernels("bad")


@pytest.mark.parametrize("operation", ["wing", "spot", "final"])
def test_get_morphological_kernels_supported_operations(operation):
    close_kernel, open_kernel = get_morphological_kernels(operation)
    assert close_kernel.ndim == 2
    assert open_kernel.ndim == 2


def test_get_width_of_black_region_returns_width_and_last():
    width, last = get_width_of_black_region(np.array([4, 5, 6, 9]), first=4)

    assert width == 2
    assert last == 6


def test_find_spot_contour_returns_none_when_contour_below_area_threshold():
    image = np.full((40, 40, 3), 255, dtype=np.uint8)
    image[15:20, 15:20] = 0
    wing_contour = np.array([[[5, 5]], [[35, 5]], [[35, 35]], [[5, 35]]], dtype=np.int32)

    contour = find_spot_contour(
        image=image,
        wing_contour=wing_contour,
        bin_thresh=120,
        min_black_pixels=1,
        min_black_width=1,
        median_blur_ksize=3,
        close_kernel_hori=3,
        close_kernel_vert=3,
        open_kernel_hori=3,
        open_kernel_vert=3,
        contour_area_threshold=10_000,
    )

    assert contour is None


def test_find_spot_contour_returns_contour_when_valid(monkeypatch):
    contour = np.array([[[5, 5]], [[30, 5]], [[30, 30]], [[5, 30]]], dtype=np.int32)

    monkeypatch.setattr("entity.spot_detector.tools.binary_spot", lambda image, bin_thresh: np.full((40, 40), 255, dtype=np.uint8))
    monkeypatch.setattr("entity.spot_detector.tools.shrink_hull", lambda wing_contour: wing_contour)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.bitwise_not", lambda img: img)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.fillPoly", lambda *args, **kwargs: None)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.bitwise_and", lambda a, b: a)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.morphologyEx", lambda img, op, kernel: img)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.findContours", lambda img, mode, method: ([contour], None))

    wing_contour = np.array([[[3, 3]], [[35, 3]], [[35, 35]], [[3, 35]]], dtype=np.int32)
    out = find_spot_contour(
        image=np.zeros((40, 40, 3), dtype=np.uint8),
        wing_contour=wing_contour,
        bin_thresh=120,
        min_black_pixels=1,
        min_black_width=1,
        median_blur_ksize=3,
        close_kernel_hori=3,
        close_kernel_vert=3,
        open_kernel_hori=3,
        open_kernel_vert=3,
        contour_area_threshold=1,
    )

    assert out is not None


def test_find_spot_contour_adjusted_threshold_branch(monkeypatch):
    contour = np.array([[[5, 5]], [[30, 5]], [[30, 30]], [[5, 30]]], dtype=np.int32)

    monkeypatch.setattr("entity.spot_detector.tools.binary_spot", lambda image, bin_thresh: np.full((40, 40), 255, dtype=np.uint8))
    monkeypatch.setattr("entity.spot_detector.tools.shrink_hull", lambda wing_contour: wing_contour)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.bitwise_not", lambda img: img)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.fillPoly", lambda *args, **kwargs: None)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.bitwise_and", lambda a, b: a)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.morphologyEx", lambda img, op, kernel: img)
    monkeypatch.setattr("entity.spot_detector.tools.cv2.findContours", lambda img, mode, method: ([contour], None))

    wing_contour = np.array([[[3, 3]], [[35, 3]], [[35, 35]], [[3, 35]]], dtype=np.int32)
    out = find_spot_contour(
        image=np.zeros((40, 40, 3), dtype=np.uint8),
        wing_contour=wing_contour,
        bin_thresh=120,
        min_black_pixels=1,
        min_black_width=1,
        median_blur_ksize=3,
        close_kernel_hori=3,
        close_kernel_vert=3,
        open_kernel_hori=3,
        open_kernel_vert=3,
        contour_area_threshold=1,
        adjust_bin_thresh=True,
        wing_height_percentage_threshold=1.1,
    )

    assert out is not None
