from abc import ABC, abstractmethod
from use_case.detection.detection_input_data import DetectionInputData
from use_case.detection.detection_output_boundary import DetectionOutputBoundary

class DetectionInputBoundary(ABC):
    """
    The input boundary interface for the detection use case.
    """
    _OutputBoundary: DetectionOutputBoundary
    _data: dict[str, list[str]] # stores results

    @abstractmethod
    def execute(self, input: DetectionInputData) -> None:
        """Executes the detection use case."""