import traceback

from PyQt5 import QtCore

from use_case.detection.adapters.detection_controller import DetectionController

STAGE_LOADING = "Loading models"


class DetectionWorker(QtCore.QThread):
    """
    Runs detection off the UI thread so the window stays responsive.
    Progress and results arrive through the presenter's signals;
    errors raised before the interactor starts (e.g. unreadable model files) are reported through `error`.
    """

    progress = QtCore.pyqtSignal(str, int, int)
    error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        controller: DetectionController,
        input_path: str,
        output_path: str,
        file_paths: dict[str, str],
        parameters: dict[str, float],
        parent: QtCore.QObject | None = None,
    ):
        super().__init__(parent)
        self._controller = controller
        self._args = (input_path, output_path, file_paths, parameters)

    def run(self) -> None:
        try:
            self.progress.emit(STAGE_LOADING, 0, 0)
            self._controller.run(*self._args)
        except Exception:
            self.error.emit(traceback.format_exc())

    def cancel(self) -> None:
        self._controller.cancel()
