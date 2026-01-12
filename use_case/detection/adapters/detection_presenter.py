from PyQt5 import QtWidgets
from use_case.detection.detection_output_boundary import DetectionOutputBoundary
from use_case.detection.detection_output_data import DetectionOutputData

class DetectionPresenter(DetectionOutputBoundary):
    """
    The presenter class for the detection use case.
    Implements the DetectionOutputBoundary interface.
    Displays success and error messages using message boxes.
    """

    def __init__(self, ui: QtWidgets.QMainWindow):
        self._ui = ui

    def prepare_success_view(self, output: DetectionOutputData) -> None:
        """Prepares the success view for the detection output."""
        success_message = f"Detection completed successfully for {len(output.success)} images."
        errors_message = f"Detection failed for {len(output.errors)} images."
        if output.success:
            success_message += f"\nSuccessful image IDs: {', '.join(output.success)}"
        if output.errors:
            errors_message += f"\nFailed image IDs: {', '.join(output.errors)}"
            success_message += f"\n\n{errors_message}"
        QtWidgets.QMessageBox.information(self._ui, "Detection Success", success_message)

    def prepare_fail_view(self, error_message: str) -> None:
        """Prepares the fail view for the detection output."""
        QtWidgets.QMessageBox.critical(self._ui, "Detection Failed", error_message)