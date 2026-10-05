from abc import ABC, abstractmethod
from use_case.detection.detection_output_data import DetectionOutputData

class DetectionOutputBoundary(ABC):
    """
    The output boundary interface for the detection use case.
    """
    @abstractmethod
    def prepare_progress_view(self, stage: str, completed: int, total: int) -> None:
        """Reports progress of the current pipeline stage.
        A total of 0 means the stage has no measurable progress (busy indicator).
        May be called from worker threads."""

    @abstractmethod
    def prepare_success_view(self, output: DetectionOutputData) -> None:
        """Prepares the success view for the detection output."""

    @abstractmethod
    def prepare_fail_view(self, error_message: str) -> None:
        """Prepares the fail view for the detection output."""
