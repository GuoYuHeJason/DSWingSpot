import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from app.main_ui import MainManager
from use_case.detection.adapters.detection_controller import DetectionController
from use_case.detection.detection_interactor import DetectionInteractor
from use_case.detection.adapters.detection_presenter import DetectionPresenter

# have to convert and move the training data!!!!!!!!, make the resources folder in spotSize

#make app
app = QtWidgets.QApplication(sys.argv)

# make main ui manager
main_ui_manager = MainManager()

# make use cases
detection_presenter = DetectionPresenter(main_ui_manager)
detection_interactor = DetectionInteractor(detection_presenter)
detection_controller = DetectionController(detection_interactor)

main_ui_manager.set_detection_controller(detection_controller)

# show main window
main_ui_manager.show()
app.exec_()