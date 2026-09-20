import numpy as np
from PIL import Image

from entity.wing_detector.tools import find_contour, crop_contour


def _rect_contour(x1, y1, x2, y2):
    return np.array([[[x1, y1]], [[x2, y1]], [[x2, y2]], [[x1, y2]]], dtype=np.int32)


def test_find_contour_returns_largest_contour_from_numpy_image():
    image = np.zeros((40, 40), dtype=np.uint8)
    image[2:10, 2:10] = 255
    image[15:35, 15:35] = 255

    contour = find_contour(image)

    assert contour is not None
    x_values = contour[:, :, 0]
    y_values = contour[:, :, 1]
    assert x_values.min() >= 15
    assert y_values.min() >= 15


def test_find_contour_accepts_pil_image():
    image = np.zeros((20, 20), dtype=np.uint8)
    image[5:15, 5:15] = 255
    pil_image = Image.fromarray(image)

    contour = find_contour(pil_image)

    assert contour is not None


def test_crop_contour_splits_when_line_intersects():
    contour = _rect_contour(0, 0, 20, 20)

    split = crop_contour(contour, (10, -5), (10, 25))

    assert len(split) == 2


def test_crop_contour_returns_original_when_not_split():
    contour = _rect_contour(0, 0, 20, 20)

    split = crop_contour(contour, (-5, -5), (-5, 25))

    assert len(split) == 1
    assert np.array_equal(split[0], contour)
