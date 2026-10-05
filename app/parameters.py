"""
Definitions of the detection parameters shown in the UI.
Keys match the parameter names expected by DetectionController and the spot detector.
"""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ParameterSpec:
    key: str
    label: str
    kind: str  # "int", "float" or "bool"
    default: Any
    tooltip: str
    minimum: float = 0
    maximum: float = 1_000_000
    step: float = 1
    decimals: int = 2
    unit: str = ""


@dataclass(frozen=True)
class ParameterGroup:
    title: str
    description: str
    parameters: list[ParameterSpec] = field(default_factory=list)
    advanced: bool = False


# over-detection reference methods, in the priority order used by the spot detector
OVERDETECTION_METHODS: dict[str, str] = {
    "wing_height_percent": "Percentage of wing height",
    "left_most_point_adjustment": "Offset from left-most wing point",
    "centroid_adjustment": "Offset from wing centroid",
}
OVERDETECTION_METHOD_KEY = "overdetection_method"
DEFAULT_OVERDETECTION_METHOD = "wing_height_percent"


PARAMETER_GROUPS: list[ParameterGroup] = [
    ParameterGroup(
        "Scale calibration",
        "Images are rescaled using the scale bar so that measurements are comparable across images.",
        [
            ParameterSpec(
                "bar_length", "Scale bar length", "float", 500,
                "Real-world length of the scale bar in your images.",
                minimum=0.01, maximum=1_000_000, step=10, decimals=2, unit="µm",
            ),
            ParameterSpec(
                "target_scale", "Target scale", "float", 1,
                "Micrometres per pixel after resizing. With 1, areas are reported in µm².\n"
                "Increase (e.g. to 10) if images become too large to process.",
                minimum=0.001, maximum=1000, step=0.5, decimals=3, unit="µm/px",
            ),
        ],
    ),
    ParameterGroup(
        "Landmarks",
        "The two landmarks used to cut the wing outline at the hinge.",
        [
            ParameterSpec(
                "landmark1", "First landmark", "int", 1,
                "Index of the first landmark predicted by the shape predictor (starting at 0).",
                minimum=0, maximum=99,
            ),
            ParameterSpec(
                "landmark2", "Second landmark", "int", 7,
                "Index of the second landmark predicted by the shape predictor (starting at 0).",
                minimum=0, maximum=99,
            ),
        ],
    ),
    ParameterGroup(
        "Spot detection",
        "How dark regions inside the wing are recognised as the spot.",
        [
            ParameterSpec(
                "bin_thresh", "Darkness threshold", "int", 116,
                "Grey level (0–255) below which pixels count as spot.\n"
                "Increase to detect lighter spots, decrease if too much of the wing is detected.",
                minimum=0, maximum=255, unit="grey level",
            ),
            ParameterSpec(
                "ostu_threshold", "Start from automatic (Otsu) threshold", "bool", False,
                "Ignore the darkness threshold above and start from a threshold computed per image with Otsu's method.",
            ),
            ParameterSpec(
                "min_spot_area", "Minimum spot area", "int", 10000,
                "Detected regions smaller than this are ignored (image reported as having no spot).",
                minimum=0, maximum=100_000_000, step=500, unit="px²",
            ),
        ],
    ),
    ParameterGroup(
        "Over-detection correction",
        "Retry with a lower threshold when the detected spot extends too far down the wing.",
        [
            ParameterSpec(
                "adjust_bin_thresh", "Correct over-detected spots", "bool", False,
                "When the lowest point of the spot is below the reference height, lower the threshold and try again.",
            ),
            ParameterSpec(
                "wing_height_percent", "Wing height fraction", "float", 0.4,
                "Spots reaching lower than this fraction of the wing height (from the top) are over-detected.",
                minimum=0, maximum=1, step=0.05, decimals=2,
            ),
            ParameterSpec(
                "left_most_point_adjustment", "Offset from left-most point", "int", -100,
                "Reference height relative to the left-most wing point. Negative moves it up, positive down.",
                minimum=-100_000, maximum=100_000, step=10, unit="px",
            ),
            ParameterSpec(
                "centroid_adjustment", "Offset from centroid", "int", 300,
                "Reference height relative to the centroid. Negative moves it up, positive down.",
                minimum=-100_000, maximum=100_000, step=10, unit="px",
            ),
            ParameterSpec(
                "adjust_rate", "Threshold reduction factor", "float", 0.9,
                "The threshold is multiplied by this factor on every retry.",
                minimum=0.05, maximum=0.99, step=0.05, decimals=2,
            ),
        ],
    ),
    ParameterGroup(
        "Noise filtering",
        "Image cleanup applied before the spot outline is extracted. Rarely needs changing.",
        [
            ParameterSpec(
                "min_black_pixels", "Minimum dark pixels per column", "int", 94,
                "Columns with fewer dark pixels than this are cleared.",
                minimum=0, maximum=100_000, unit="px",
            ),
            ParameterSpec(
                "min_black_width", "Minimum dark run length", "int", 32,
                "Vertical dark runs shorter than this are cleared (removes veins).",
                minimum=0, maximum=100_000, unit="px",
            ),
            ParameterSpec(
                "median_blur_ksize", "Median blur size", "int", 5,
                "Kernel size of the median blur. Must be odd.",
                minimum=1, maximum=99, step=2, unit="px",
            ),
            ParameterSpec(
                "close_kernel_hori", "Closing kernel width", "int", 7,
                "Width of the morphological closing kernel (fills gaps).",
                minimum=1, maximum=999, unit="px",
            ),
            ParameterSpec(
                "close_kernel_vert", "Closing kernel height", "int", 11,
                "Height of the morphological closing kernel (fills gaps).",
                minimum=1, maximum=999, unit="px",
            ),
            ParameterSpec(
                "open_kernel_hori", "Opening kernel width", "int", 7,
                "Width of the morphological opening kernel (removes specks).",
                minimum=1, maximum=999, unit="px",
            ),
            ParameterSpec(
                "open_kernel_vert", "Opening kernel height", "int", 7,
                "Height of the morphological opening kernel (removes specks).",
                minimum=1, maximum=999, unit="px",
            ),
        ],
        advanced=True,
    ),
]

ALL_PARAMETERS: dict[str, ParameterSpec] = {
    spec.key: spec for group in PARAMETER_GROUPS for spec in group.parameters
}


def default_parameters() -> dict[str, Any]:
    values: dict[str, Any] = {key: spec.default for key, spec in ALL_PARAMETERS.items()}
    values[OVERDETECTION_METHOD_KEY] = DEFAULT_OVERDETECTION_METHOD
    return values


def to_detection_parameters(values: dict[str, Any]) -> dict[str, float]:
    """
    Converts UI values to the parameter dict expected by the controller.
    The spot detector uses the first non-zero over-detection reference, so the unselected ones are zeroed.
    """
    method: Optional[str] = values.get(OVERDETECTION_METHOD_KEY, DEFAULT_OVERDETECTION_METHOD)
    result: dict[str, float] = {}
    for key, spec in ALL_PARAMETERS.items():
        value = values.get(key, spec.default)
        if key in OVERDETECTION_METHODS and key != method:
            value = 0
        result[key] = float(value) if spec.kind != "bool" else bool(value)
    return result
