import json

from use_case.detection.tools import save_results, read_dictionary


def test_save_and_read_results_integration(tmp_path):
    payload = {
        "image_id": ["img1", "img2"],
        "wing_area": ["100", "200"],
        "spot_area": ["10", "40"],
        "spot_ratio": ["0.1", "0.2"],
    }

    save_results(str(tmp_path), payload, filename="wing_spot_results")

    loaded = read_dictionary(str(tmp_path / "wing_spot_results.json"))

    assert loaded == payload
    csv_text = (tmp_path / "wing_spot_results.csv").read_text(encoding="utf-8")
    assert "image_id" in csv_text
    assert "img2" in csv_text
