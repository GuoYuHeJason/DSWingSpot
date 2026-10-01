import sys
from PyQt5 import QtCore, QtWidgets
from app.main_ui import MainManager
from app.resources import APP_NAME
from app.style import apply_style
from use_case.detection.adapters.detection_controller import DetectionController
from use_case.detection.detection_interactor import DetectionInteractor
from use_case.detection.adapters.detection_presenter import DetectionPresenter, DetectionSignals

import multiprocessing


#  must protect the main entry point of your script using if __name__ == '__main__':
if __name__ == '__main__':
    multiprocessing.freeze_support() # for pyinstaller on Windows
    #make app

    # Enable High DPI scaling
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    # Ensure icons and pixmaps also scale correctly
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    apply_style(app)

    # make use cases, the presenter reports to the UI through Qt signals
    detection_signals = DetectionSignals()
    detection_presenter = DetectionPresenter(detection_signals)
    detection_interactor = DetectionInteractor(detection_presenter)
    detection_controller = DetectionController(detection_interactor)

    # make main ui manager
    main_ui_manager = MainManager(detection_signals)
    main_ui_manager.set_detection_controller(detection_controller)

    # show main window
    main_ui_manager.show()
    app.exec_()
