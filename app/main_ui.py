import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
import sys
import os
from os import path
from use_case.detection.adapters.detection_controller import DetectionController

"pyqt5-tools designer"

# class MainWindow(QtWidgets.QMainWindow):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         uic.loadUi("main_window.ui", self)


# app = QtWidgets.QApplication(sys.argv)
# window = MainWindow()
# window.show()
# app.exec_()


from .main_window import Ui_MainWindow

# advance options: dialog scroll window, get the ones I think important
# ex: torlarence of variation in shape: samll the value, more likely the detected contour will look like the training contours.

    # have something simlar to python print (a scroll that gets added) to show the status of wings, only in detect use case

class MainManager(QtWidgets.QMainWindow, Ui_MainWindow):

    _detect_controller: DetectionController

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.connect_Signals_Slots()

    def set_detection_controller(self, controller: DetectionController):
        self._detect_controller = controller
    
    def connect_Signals_Slots(self):
        self.detectionControllerButton.clicked.connect(self.call_detect_controller) # give the function as param, not calling the function or giving the returned value as param

    def call_detect_controller(self):
        try:
            input_path, output_path, file_paths, parameters = self.get_detection_inputs()
        except FileNotFoundError as e:
            QtWidgets.QMessageBox.warning(self, "Path Not Found", str(e))
            return

        self._detect_controller.run(input_path, output_path, file_paths, parameters)

    #helper function to get dict from scroll layout
    def get_dict_from_scroll_layout(self, layout: QtWidgets.QVBoxLayout) -> dict[str, str] | dict[str, float]:
        result = {}
        for i in range(layout.count()):
            # loop through each widget in the layout
            item = layout.itemAt(i)
            # check if item is a widget
            if item is None:
                continue
            widget = item.widget()
            if widget:
                # a widget is expected to have a label and a text edit
                label = widget.findChild(QtWidgets.QLabel)
                text_edit = widget.findChild(QtWidgets.QTextEdit)
                if label and text_edit:
                    text = text_edit.toPlainText()
                    try :
                        # try to convert to float
                        value = float(text)
                        result[label.text()] = value
                    except ValueError:
                        # if not a float, keep as string
                        result[label.text()] = text.strip()

        return result

    def get_parameters_dict(self) -> dict[str, float]:
        return self.get_dict_from_scroll_layout(self.verticalLayout) # type: ignore
    
    def get_file_paths_dict(self) -> dict[str, str]:
        file_path_dict = self.get_dict_from_scroll_layout(self.verticalLayout_2) # type: ignore
        file_path_dict: dict[str, str]
        for key, path in file_path_dict.items():
            file_path_dict[key] = self.str_to_path(path)
        return file_path_dict
    
    def str_to_path(self, text: str) -> str:
        """
        Convert a string to a valid path, handling various formatting issues such as:
        - Removing leading/trailing spaces
        - Removing starting/ending quotes
        - Converting Windows-style paths to macOS-compatible paths
        """
        # Strip leading and trailing spaces
        text = text.strip()

        # Remove starting and ending quotes, if any
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        elif text.startswith("'") and text.endswith("'"):
            text = text[1:-1]

        # Normalize the path to handle different OS formats
        normalized_path = os.path.normpath(text)

        return normalized_path
    
    def get_detection_inputs(self) -> tuple[str, str, dict[str, str], dict[str, float]]:
        # assuming each file widget has a label and a text edit
        file_paths = self.get_file_paths_dict()
        input_path = self.str_to_path(self.detectionInputlineEdit.text())
        output_path = self.str_to_path(self.detectionOutputlineEdit.text())
        parameters = self.get_parameters_dict()

        # check that all paths exist
        # check input and output paths
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input path does not exist: {input_path}")
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output path does not exist: {output_path}")
        for key, path in file_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path for {key} does not exist: {path}")

        return input_path, output_path, file_paths, parameters

# presenter needs the ui, give when constructing presenter.

