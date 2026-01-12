from typing import Any

from entity.bg_remover.engine import U2NetBGRemover
from entity.image_resizing.resizer import ImageResizer
from entity.shape_predictor.predictor import ShapePredictor
from entity.spot_detector.detector import SpotDetector
from entity.wing_detector.detector import WingDetector

class DetectionInputData:
    """
    The input data for the detection use case.
    """
    # attributes
    input_path: str
    output_path: str
    shape_predictor: ShapePredictor
    bg_removal_model: U2NetBGRemover
    image_resizer: ImageResizer
    wing_detector: WingDetector
    spot_detector: SpotDetector
    landmark1_x: str
    landmark1_y: str
    landmark2_x: str
    landmark2_y: str

    def __init__(self,
                 input_path: str,
                 output_path: str,
                 shape_predictor: ShapePredictor,
                 bg_removal_model: U2NetBGRemover,
                 image_resizer: ImageResizer,
                 wing_detector: WingDetector,
                 spot_detector: SpotDetector,
                 landmark1_x: str,
                 landmark1_y: str,
                 landmark2_x: str,
                 landmark2_y: str) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.shape_predictor = shape_predictor
        self.bg_removal_model = bg_removal_model
        self.image_resizer = image_resizer
        self.wing_detector = wing_detector
        self.spot_detector = spot_detector
        self.landmark1_x = landmark1_x
        self.landmark1_y = landmark1_y
        self.landmark2_x = landmark2_x
        self.landmark2_y = landmark2_y
