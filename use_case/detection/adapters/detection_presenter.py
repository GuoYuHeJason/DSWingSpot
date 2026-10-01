from PyQt5 import QtCore
from use_case.detection.detection_output_boundary import DetectionOutputBoundary
from use_case.detection.detection_output_data import DetectionOutputData

class DetectionSignals(QtCore.QObject):
    """Qt signals carrying detection updates to the UI."""
    progress = QtCore.pyqtSignal(str, int, int)  # stage, completed, total
    succeeded = QtCore.pyqtSignal(object)  # DetectionOutputData
    failed = QtCore.pyqtSignal(str)  # error message

class DetectionPresenter(DetectionOutputBoundary):
    """
    The presenter class for the detection use case.
    Implements the DetectionOutputBoundary interface.
    Detection runs on a worker thread, so results are forwarded to the UI through Qt signals,
    which Qt delivers on the UI thread.
    """

    def __init__(self, signals: DetectionSignals):
        self.signals = signals

    def prepare_progress_view(self, stage: str, completed: int, total: int) -> None:
        self.signals.progress.emit(stage, completed, total)

    def prepare_success_view(self, output: DetectionOutputData) -> None:
        """Prepares the success view for the detection output."""
        self.signals.succeeded.emit(output)

    def prepare_fail_view(self, error_message: str) -> None:
        """Prepares the fail view for the detection output."""
        self.signals.failed.emit(error_message)
