import json
from pathlib import Path

import numpy as np
import pytest

from use_case.detection.tools import (
    read_image,
    write_image,
    read_dictionary,
    write_dictionary,
    write_csv,
    save_results,
)


def test_read_image_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_image(str(tmp_path / "missing.png"))


def test_dictionary_round_trip(tmp_path):
    path = tmp_path / "data.json"
    payload = {"a": 1}

    write_dictionary(str(path), payload)
    loaded = read_dictionary(str(path))

    assert loaded == payload


def test_read_dictionary_invalid_type_raises(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="expected a dictionary"):
        read_dictionary(str(path))


def test_write_csv_requires_equal_lengths(tmp_path):
    with pytest.raises(ValueError, match="same length"):
        write_csv(str(tmp_path / "bad.csv"), {"a": ["1"], "b": ["1", "2"]})


def test_save_results_writes_csv_and_json(tmp_path):
    data = {"image_id": ["img1"], "wing_area": ["10"], "spot_area": ["2"], "spot_ratio": ["0.2"]}

    save_results(str(tmp_path), data, filename="result")

    assert (tmp_path / "result.csv").exists()
    assert (tmp_path / "result.json").exists()


def test_write_image_creates_file(tmp_path):
    image = np.zeros((5, 5, 3), dtype=np.uint8)

    write_image("img", image, str(tmp_path), format="png")

    assert (tmp_path / "img.png").exists()
