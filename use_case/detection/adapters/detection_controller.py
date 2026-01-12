from use_case.detection.detection_input_data import DetectionInputData
from use_case.detection.detection_input_boundary import DetectionInputBoundary

from entity.bg_remover.engine import U2NetBGRemover
from entity.image_resizing.resizer import ImageResizer
from entity.shape_predictor.predictor import ShapePredictor
from entity.wing_detector.detector import WingDetector
from entity.spot_detector.detector import AlgSpotDetector

from use_case.detection.tools import read_dictionary
import PIL.Image

class DetectionController:
    """
    Controller for detection use case. Called by UI.
    Packages input data and sends to input boundary.
    """
    input_boundary: DetectionInputBoundary

    def __init__(self, input_boundary: DetectionInputBoundary):
        self.input_boundary = input_boundary

    def run(
        self,
        input_path: str,
        output_path: str,
        file_paths: dict[str, str],
        parameters: dict[str, float]
    ) -> None:
        # load image
        scale_bar_template = PIL.Image.open(file_paths["scale_bar_template"])

        input_data = DetectionInputData(
                input_path=input_path,
                output_path=output_path,
                shape_predictor=ShapePredictor(file_paths["shape_predictor"]),
                bg_removal_model=U2NetBGRemover(file_paths["bg_removal_model"]),
                image_resizer=ImageResizer(scale_bar_template, parameters["bar_length"], parameters['target_scale']),
                wing_detector=WingDetector(),
                spot_detector=AlgSpotDetector(parameters),
                landmark1_x=f"X{int(parameters['landmark1'])}", # 3
                landmark1_y=f"Y{int(parameters['landmark1'])}",
                landmark2_x=f"X{int(parameters['landmark2'])}", # 8
                landmark2_y=f"Y{int(parameters['landmark2'])}",
        )
        self.input_boundary.execute(input_data)