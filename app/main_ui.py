import json
import os
import time
from datetime import datetime
from typing import Any, Optional

from PyQt5 import QtCore, QtGui, QtSvg, QtWidgets

from app import style
from app.detection_worker import STAGE_LOADING, DetectionWorker
from app.parameters import to_detection_parameters
from app.resources import (
    APP_NAME, ASSET_FILES, IMAGE_EXTENSIONS, PROJECT_URL,
    default_asset_folders, find_assets, icon_path,
)
from app.widgets import Card, ImagePreview, ParameterForm, PathField, StageList, StatusLabel, ThumbnailStrip
from use_case.detection.adapters.detection_controller import DetectionController
from use_case.detection.adapters.detection_presenter import DetectionSignals
from use_case.detection.detection_interactor import STAGES
from use_case.detection.detection_output_data import DetectionOutputData

RESULTS_FOLDER_NAME = "DSwingSpot_results"
RESULTS_CSV = "wing_spot_results.csv"
RUN_SETTINGS_FILE = "run_settings.json"

PAGE_SETUP, PAGE_PARAMETERS, PAGE_RUN, PAGE_RESULTS = range(4)


def list_images(folder: str) -> list[str]:
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    return [
        os.path.join(folder, name) for name in names
        if name.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(folder, name))
    ]


def short_path(path: str) -> str:
    """Last two components of a path, for display where space is limited (full path goes in a tooltip)."""
    if not path:
        return "—"
    parts = os.path.normpath(path).split(os.sep)
    return path if len(parts) <= 3 else os.path.join("…", *parts[-2:])


def page_header(title: str) -> QtWidgets.QWidget:
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 6)
    title_label = QtWidgets.QLabel(title)
    title_label.setObjectName("pageTitle")
    layout.addWidget(title_label)
    return widget


def logo_pixmap(height: int) -> QtGui.QPixmap:
    """The fly logo, drawn as vectors so it stays sharp on high-DPI screens."""
    renderer = QtSvg.QSvgRenderer(icon_path("fly.svg"))
    view = renderer.viewBoxF()
    width = height * view.width() / view.height()
    ratio = QtWidgets.QApplication.instance().devicePixelRatio()
    pixmap = QtGui.QPixmap(round(width * ratio), round(height * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    renderer.render(painter, QtCore.QRectF(0, 0, width, height))
    painter.end()
    return pixmap


class MainManager(QtWidgets.QMainWindow):
    """Main window: a step-by-step workflow from choosing images to reviewing results."""

    _detect_controller: DetectionController

    def __init__(self, signals: DetectionSignals, settings: Optional[QtCore.QSettings] = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._signals = signals
        self._settings = settings if settings is not None else QtCore.QSettings(APP_NAME, APP_NAME)
        self._worker: Optional[DetectionWorker] = None
        self._run_started = 0.0
        self._run_output_path = ""
        self._run_target_scale = 1.0
        self._image_paths: list[str] = []
        self._setup_errors: list[str] = []
        self._current_stage = ""

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QtGui.QIcon(icon_path("fly.svg")))
        self.setMinimumSize(900, 640)

        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._restore_settings()
        self._validate()
        self._go_to(PAGE_SETUP)

    def set_detection_controller(self, controller: DetectionController) -> None:
        self._detect_controller = controller

    # ------------------------------------------------------------------ layout

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        self.pages = QtWidgets.QStackedWidget()
        self.pages.setObjectName("pageContainer")
        self.pages.addWidget(self._build_setup_page())
        self.pages.addWidget(self._build_parameters_page())
        self.pages.addWidget(self._build_run_page())
        self.pages.addWidget(self._build_results_page())
        root.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.status_label = QtWidgets.QLabel()
        self.statusBar().addWidget(self.status_label, 1)
        self.status_progress = QtWidgets.QProgressBar()
        self.status_progress.setFixedWidth(160)
        self.status_progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.status_progress)

    def _build_sidebar(self) -> QtWidgets.QWidget:
        sidebar = QtWidgets.QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        layout = QtWidgets.QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(4)

        logo = QtWidgets.QLabel()
        logo.setPixmap(logo_pixmap(150))
        logo.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(logo)
        layout.addSpacing(24)

        self.nav_group = QtWidgets.QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QtWidgets.QPushButton] = []
        self.nav_labels = ["Images & models", "Parameters", "Run detection", "Results"]
        self._nav_done = [False] * len(self.nav_labels)
        for index, text in enumerate(self.nav_labels):
            # "&&" shows a literal ampersand instead of a keyboard mnemonic
            button = QtWidgets.QPushButton(f"  {index + 1}   {text.replace('&', '&&')}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(QtCore.Qt.PointingHandCursor)
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)
        self.nav_group.buttonClicked[int].connect(self._go_to)

        layout.addStretch(1)
        return sidebar

    def _page(self, title: str) -> tuple[QtWidgets.QWidget, QtWidgets.QVBoxLayout, QtWidgets.QHBoxLayout]:
        """Creates a page with a scrollable body and a footer for navigation buttons."""
        page = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        body_widget = QtWidgets.QWidget()
        body = QtWidgets.QVBoxLayout(body_widget)
        body.setContentsMargins(32, 26, 32, 20)
        body.setSpacing(16)
        body.addWidget(page_header(title))
        scroll.setWidget(body_widget)
        outer.addWidget(scroll, 1)

        footer_widget = QtWidgets.QFrame()
        footer_widget.setObjectName("footer")
        footer = QtWidgets.QHBoxLayout(footer_widget)
        footer.setContentsMargins(32, 12, 32, 12)
        outer.addWidget(footer_widget)
        return page, body, footer

    def _build_setup_page(self) -> QtWidgets.QWidget:
        page, body, footer = self._page("Images & models")

        images_card = Card("Images")
        self.input_field = PathField(
            "Image folder", select_directory=True,
            placeholder="Folder containing wing images (drag a folder here)",
            tooltip="All JPG, PNG, BMP and TIFF images directly inside this folder are processed.\n"
                    "Wings should point to the left and include the scale bar.",
        )
        images_card.body.addWidget(self.input_field)
        self.thumbnails = ThumbnailStrip()
        self.thumbnails.setVisible(False)
        images_card.body.addWidget(self.thumbnails)
        self.output_field = PathField(
            "Results folder", select_directory=True,
            tooltip="Results table, annotated images and the settings used are saved here.\n"
                    "The folder is created if it does not exist.",
        )
        images_card.body.addWidget(self.output_field)
        body.addWidget(images_card)

        models_card = Card(
            "Models & calibration",
            "Files from assets.zip on the releases page, plus a scale bar image cropped from your own microscope images.",
        )
        self.find_assets_button = QtWidgets.QPushButton("Load from folder…")
        self.find_assets_button.setToolTip("Pick the extracted assets folder to fill in all model files at once.")
        models_card.header_actions.addWidget(self.find_assets_button)

        self.asset_fields: dict[str, PathField] = {}
        tooltips = {
            "scale_bar_template": "A tightly cropped, high-contrast image of the scale bar, used to find the scale bar in every image.",
            "bg_removal_model": "U²-Net model (.pth) used to separate the wing from the background.",
            "shape_predictor": "dlib shape predictor (.dat) that places anatomical landmarks on the wing.",
        }
        template_row = QtWidgets.QHBoxLayout()
        fields_column = QtWidgets.QVBoxLayout()
        fields_column.setSpacing(12)
        for key, (label, file_filter, _) in ASSET_FILES.items():
            field = PathField(label, select_directory=False, file_filter=file_filter, tooltip=tooltips[key])
            self.asset_fields[key] = field
            fields_column.addWidget(field)
        template_row.addLayout(fields_column, 1)
        self.template_preview = QtWidgets.QLabel()
        self.template_preview.setFixedSize(150, 70)
        self.template_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.template_preview.setToolTip("Scale bar template preview")
        self.template_preview.setStyleSheet("background: #eef1f4; border-radius: 6px;")
        template_row.addWidget(self.template_preview, 0, QtCore.Qt.AlignTop)
        models_card.body.addLayout(template_row)
        body.addWidget(models_card)
        body.addStretch(1)

        self.setup_summary = StatusLabel()
        footer.addWidget(self.setup_summary, 1)
        self.setup_next = QtWidgets.QPushButton("Next: Parameters  →")
        self.setup_next.setObjectName("primaryButton")
        self.setup_next.clicked.connect(lambda: self._go_to(PAGE_PARAMETERS))
        footer.addWidget(self.setup_next)
        return page

    def _build_parameters_page(self) -> QtWidgets.QWidget:
        page, body, footer = self._page("Parameters")
        toolbar = QtWidgets.QHBoxLayout()
        self.load_preset_button = QtWidgets.QPushButton("Load preset…")
        self.load_preset_button.setToolTip(f"Load parameters from a preset or from a previous run's {RUN_SETTINGS_FILE}.")
        self.save_preset_button = QtWidgets.QPushButton("Save preset…")
        self.restore_defaults_button = QtWidgets.QPushButton("Restore defaults")
        self.modified_label = QtWidgets.QLabel()
        self.modified_label.setObjectName("hint")
        toolbar.addWidget(self.load_preset_button)
        toolbar.addWidget(self.save_preset_button)
        toolbar.addWidget(self.restore_defaults_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.modified_label)
        body.addLayout(toolbar)

        self.parameter_form = ParameterForm()
        body.addWidget(self.parameter_form)

        back = QtWidgets.QPushButton("←  Back")
        back.clicked.connect(lambda: self._go_to(PAGE_SETUP))
        footer.addWidget(back)
        footer.addStretch(1)
        next_button = QtWidgets.QPushButton("Next: Run  →")
        next_button.setObjectName("primaryButton")
        next_button.clicked.connect(lambda: self._go_to(PAGE_RUN))
        footer.addWidget(next_button)
        return page

    def _build_run_page(self) -> QtWidgets.QWidget:
        page, body, footer = self._page("Run detection")

        summary_card = Card("Summary")
        self.run_summary = QtWidgets.QFormLayout()
        self.run_summary.setHorizontalSpacing(24)
        self.run_summary.setVerticalSpacing(6)
        summary_card.body.addLayout(self.run_summary)
        self.run_issues = StatusLabel()
        summary_card.body.addWidget(self.run_issues)
        buttons = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start detection")
        self.start_button.setObjectName("primaryButton")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch(1)
        summary_card.body.addLayout(buttons)

        progress_card = Card("Progress")
        self.stage_list = StageList([STAGE_LOADING, *STAGES])
        progress_card.body.addWidget(self.stage_list)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        progress_card.body.addWidget(self.progress_bar)
        self.progress_label = QtWidgets.QLabel("Not started")
        self.progress_label.setObjectName("hint")
        progress_card.body.addWidget(self.progress_label)
        progress_card.body.addStretch(1)

        cards = QtWidgets.QHBoxLayout()
        cards.setSpacing(16)
        cards.addWidget(summary_card, 1)
        cards.addWidget(progress_card, 1)
        body.addLayout(cards)

        log_card = Card("Log")
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(140)
        self.log_view.setMaximumBlockCount(5000)
        log_card.body.addWidget(self.log_view)
        body.addWidget(log_card, 1)

        back = QtWidgets.QPushButton("←  Back")
        back.clicked.connect(lambda: self._go_to(PAGE_PARAMETERS))
        footer.addWidget(back)
        footer.addStretch(1)
        self.view_results_button = QtWidgets.QPushButton("View results  →")
        self.view_results_button.setObjectName("primaryButton")
        self.view_results_button.setEnabled(False)
        self.view_results_button.clicked.connect(lambda: self._go_to(PAGE_RESULTS))
        footer.addWidget(self.view_results_button)

        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._update_progress_label)
        return page

    def _build_results_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(32, 26, 32, 20)
        outer.setSpacing(14)
        outer.addWidget(page_header("Results"))

        top = QtWidgets.QHBoxLayout()
        self.results_summary = QtWidgets.QLabel("No results yet. Run detection first.")
        self.results_summary.setStyleSheet("font-weight: 600;")
        top.addWidget(self.results_summary, 1)
        top.addWidget(QtWidgets.QLabel("Show"))
        self.results_filter = QtWidgets.QComboBox()
        self.results_filter.addItems(["All images", "Measured", "No spot detected", "Failed"])
        top.addWidget(self.results_filter)
        outer.addLayout(top)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.results_table = QtWidgets.QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(
            ["Image", "Status", "Wing area", "Spot area", "Ratio"]
        )
        self.results_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        self.results_table.setShowGrid(False)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        self.results_table.setMinimumWidth(420)
        splitter.addWidget(self.results_table)

        preview_panel = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 0, 0, 0)
        self.preview_title = QtWidgets.QLabel()
        self.preview_title.setStyleSheet("font-weight: 600;")
        preview_layout.addWidget(self.preview_title)
        self.preview = ImagePreview()
        self.preview.show_message("Select an image to preview")
        preview_layout.addWidget(self.preview, 1)
        self.preview_detail = StatusLabel()
        preview_layout.addWidget(self.preview_detail)
        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([650, 350])
        outer.addWidget(splitter, 1)

        actions = QtWidgets.QHBoxLayout()
        self.open_folder_button = QtWidgets.QPushButton("Open results folder")
        self.open_csv_button = QtWidgets.QPushButton("Open results table (CSV)")
        self.new_run_button = QtWidgets.QPushButton("Adjust parameters and run again")
        for button in (self.open_folder_button, self.open_csv_button):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch(1)
        actions.addWidget(self.new_run_button)
        outer.addLayout(actions)
        return page

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = file_menu.addAction("Choose image folder…")
        open_action.setShortcut(QtGui.QKeySequence.Open)
        open_action.triggered.connect(lambda: (self._go_to(PAGE_SETUP), self.input_field.browse()))
        file_menu.addSeparator()
        self.load_preset_action = file_menu.addAction("Load parameter preset…")
        self.load_preset_action.triggered.connect(self._load_preset)
        file_menu.addAction("Save parameter preset…").triggered.connect(self._save_preset)
        file_menu.addSeparator()
        self.open_results_action = file_menu.addAction("Open results folder")
        self.open_results_action.setEnabled(False)
        self.open_results_action.triggered.connect(self._open_results_folder)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut(QtGui.QKeySequence.Quit)
        quit_action.setMenuRole(QtWidgets.QAction.QuitRole)
        quit_action.triggered.connect(self.close)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("User guide").triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"{PROJECT_URL}#usage"))
        )
        help_menu.addAction("Troubleshooting").triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"{PROJECT_URL}#troubleshooting"))
        )
        about = help_menu.addAction(f"About {APP_NAME}")
        about.setMenuRole(QtWidgets.QAction.AboutRole)
        about.triggered.connect(self._show_about)

    def _connect_signals(self) -> None:
        self.input_field.changed.connect(self._on_input_changed)
        self.output_field.changed.connect(lambda _: self._validate())
        for field in self.asset_fields.values():
            field.changed.connect(lambda _: self._validate())
        self.find_assets_button.clicked.connect(self._choose_assets_folder)

        self.parameter_form.changed.connect(self._on_parameters_changed)
        self.load_preset_button.clicked.connect(self._load_preset)
        self.save_preset_button.clicked.connect(self._save_preset)
        self.restore_defaults_button.clicked.connect(self.parameter_form.restore_defaults)

        self.start_button.clicked.connect(self.start_detection)
        self.cancel_button.clicked.connect(self.cancel_detection)

        self.results_filter.currentIndexChanged.connect(self._apply_results_filter)
        self.results_table.itemSelectionChanged.connect(self._show_selected_result)
        self.open_folder_button.clicked.connect(self._open_results_folder)
        self.open_csv_button.clicked.connect(self._open_results_csv)
        self.new_run_button.clicked.connect(lambda: self._go_to(PAGE_PARAMETERS))

        self._signals.progress.connect(self._on_progress)
        self._signals.succeeded.connect(self._on_finished)
        self._signals.failed.connect(self._on_failed)

    # ------------------------------------------------------------------ navigation

    def _set_nav_done(self, index: int, done: bool) -> None:
        """Shows or hides the completion check on a sidebar button."""
        if self._nav_done[index] == done:
            return
        self._nav_done[index] = done
        label = self.nav_labels[index].replace("&", "&&")
        self.nav_buttons[index].setText(f"  {index + 1}   {label}{'   ✓' if done else ''}")

    def _go_to(self, index: int) -> None:
        if index == PAGE_RUN:
            self._refresh_run_summary()
        if index == PAGE_PARAMETERS:
            # Defaults are always valid, so visiting the page is what marks it reviewed.
            self._set_nav_done(PAGE_PARAMETERS, True)
        self.pages.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)

    # ------------------------------------------------------------------ setup page

    def _on_input_changed(self, path: str) -> None:
        self._image_paths = list_images(path) if path and os.path.isdir(path) else []
        self.thumbnails.set_images(self._image_paths)
        self.thumbnails.setVisible(bool(self._image_paths))
        self._validate()

    def _default_output_path(self) -> str:
        input_path = self.input_field.path()
        return os.path.join(input_path, RESULTS_FOLDER_NAME) if input_path else ""

    def output_path(self) -> str:
        return self.output_field.path() or self._default_output_path()

    def _choose_assets_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose the assets folder", os.path.expanduser("~"))
        if not folder:
            return
        found = find_assets(folder)
        for key, path in found.items():
            self.asset_fields[key].set_path(path)
        missing = [ASSET_FILES[key][0] for key in ASSET_FILES if key not in found]
        if missing:
            QtWidgets.QMessageBox.information(
                self, "Some files not found",
                f"Could not find the following in {folder}:\n\n• " + "\n• ".join(missing)
                + "\n\nPlease choose them individually.",
            )

    def _validate(self) -> None:
        """Checks all setup inputs, shows messages next to each field and updates the run button."""
        errors: list[str] = []

        input_path = self.input_field.path()
        if not input_path:
            self.input_field.set_status("", "")
            errors.append("Choose an image folder")
        elif not os.path.isdir(input_path):
            self.input_field.set_status("error", "Folder not found")
            errors.append("Image folder not found")
        elif not self._image_paths:
            self.input_field.set_status("error", "No images found (supported: JPG, PNG, BMP, TIFF)")
            errors.append("No images in the image folder")
        else:
            count = len(self._image_paths)
            self.input_field.set_status("ok", f"{count} image{'s' if count != 1 else ''} found")

        default_output = self._default_output_path()
        self.output_field.set_placeholder(
            f"Default: {default_output}" if default_output else "Defaults to a folder inside the image folder"
        )
        output_path = self.output_path()
        if not output_path:
            self.output_field.set_status("", "")
        elif os.path.exists(output_path) and not os.path.isdir(output_path):
            self.output_field.set_status("error", "This is a file, not a folder")
            errors.append("Results folder is not a folder")
        elif input_path and os.path.normcase(os.path.abspath(output_path)) == os.path.normcase(os.path.abspath(input_path)):
            self.output_field.set_status("error", "Choose a different folder: annotated images would overwrite your originals")
            errors.append("Results folder must differ from the image folder")
        elif not os.path.isdir(output_path) and not os.path.isdir(os.path.dirname(output_path)):
            self.output_field.set_status("error", "Parent folder not found")
            errors.append("Results folder location not found")
        elif os.path.isfile(os.path.join(output_path, RESULTS_CSV)):
            self.output_field.set_status("warn", "Contains previous results, which will be overwritten")
        elif not os.path.isdir(output_path):
            self.output_field.set_status("info", "Will be created when detection starts")
        else:
            self.output_field.set_status("", "")

        for key, (label, _, extensions) in ASSET_FILES.items():
            field = self.asset_fields[key]
            path = field.path()
            if not path:
                field.set_status("", "")
                errors.append(f"Choose the {label.lower()}")
            elif not os.path.isfile(path):
                field.set_status("error", "File not found")
                errors.append(f"{label} not found")
            elif not path.lower().endswith(extensions):
                field.set_status("warn", f"Unexpected file type, expected {', '.join(extensions)}")
            else:
                field.set_status("ok", os.path.basename(path))

        template = QtGui.QPixmap(self.asset_fields["scale_bar_template"].path())
        if template.isNull():
            self.template_preview.setText("No preview")
            self.template_preview.setStyleSheet(f"background: #eef1f4; border-radius: 6px; color: {style.MUTED};")
        else:
            self.template_preview.setPixmap(template.scaled(
                self.template_preview.size() - QtCore.QSize(10, 10), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            ))

        self._setup_errors = errors
        if errors:
            self.setup_summary.set_status("info", f"{len(errors)} item{'s' if len(errors) != 1 else ''} left to set up")
        else:
            self.setup_summary.set_status("ok", "Ready")
        self._set_nav_done(PAGE_SETUP, not errors)
        self._update_run_controls()
        if self.pages.currentIndex() == PAGE_RUN:
            self._refresh_run_summary()

    # ------------------------------------------------------------------ parameters page

    def _on_parameters_changed(self) -> None:
        count = self.parameter_form.modified_count()
        self.modified_label.setText(f"{count} changed from default" if count else "Using default values")
        self.restore_defaults_button.setEnabled(bool(count))

    def _load_preset(self) -> None:
        if self._worker is not None:
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load parameter preset", self._preset_directory(), "Parameter presets (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            values = data.get("parameters", data) if isinstance(data, dict) else None
            if not isinstance(values, dict):
                raise ValueError("The file does not contain parameters.")
        except (OSError, ValueError) as e:
            QtWidgets.QMessageBox.warning(self, "Could not load preset", f"{os.path.basename(path)} could not be read:\n{e}")
            return
        self.parameter_form.restore_defaults()
        unknown = self.parameter_form.set_values(values)
        self._settings.setValue("presets/directory", os.path.dirname(path))
        self._go_to(PAGE_PARAMETERS)
        message = f"Loaded parameters from {os.path.basename(path)}"
        if unknown:
            message += f" (ignored unknown: {', '.join(unknown)})"
        self.statusBar().showMessage(message, 8000)

    def _save_preset(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save parameter preset", os.path.join(self._preset_directory(), "parameters.json"),
            "Parameter presets (*.json)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"application": APP_NAME, "parameters": self.parameter_form.values()}, f, indent=2)
        except OSError as e:
            QtWidgets.QMessageBox.warning(self, "Could not save preset", str(e))
            return
        self._settings.setValue("presets/directory", os.path.dirname(path))
        self.statusBar().showMessage(f"Saved parameters to {path}", 8000)

    def _preset_directory(self) -> str:
        return str(self._settings.value("presets/directory", os.path.expanduser("~")))

    # ------------------------------------------------------------------ run page

    def _refresh_run_summary(self) -> None:
        while self.run_summary.rowCount():
            self.run_summary.removeRow(0)
        values = self.parameter_form.values()

        def add(label: str, value: str, tooltip: str = "") -> None:
            value_label = QtWidgets.QLabel(value)
            value_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setToolTip(tooltip)
            name = QtWidgets.QLabel(label)
            name.setObjectName("hint")
            self.run_summary.addRow(name, value_label)

        input_path, output_path = self.input_field.path(), self.output_path()
        add("Images", f"{len(self._image_paths)} in {short_path(input_path)}", input_path)
        add("Results folder", short_path(output_path), output_path)
        add("Scale", f"{values['bar_length']:g} µm scale bar, {values['target_scale']:g} µm/px")
        threshold = "automatic (Otsu)" if values["ostu_threshold"] else str(values["bin_thresh"])
        correction = "on" if values["adjust_bin_thresh"] else "off"
        add("Spot detection", f"threshold {threshold}, over-detection correction {correction}")
        modified = self.parameter_form.modified_count()
        add("Parameters", f"{modified} changed from default" if modified else "defaults")
        self._update_run_controls()

    def _update_run_controls(self) -> None:
        running = self._worker is not None
        if running:
            self.run_issues.set_status("", "")
        elif self._setup_errors:
            self.run_issues.set_status("error", "Before starting: " + "; ".join(self._setup_errors) + ".")
        else:
            self.run_issues.set_status("ok", "Ready to start")
        self.start_button.setEnabled(not running and not self._setup_errors)
        self.cancel_button.setEnabled(running)

    def _set_inputs_locked(self, locked: bool) -> None:
        for index in (PAGE_SETUP, PAGE_PARAMETERS):
            page = self.pages.widget(index)
            for child in page.findChildren(QtWidgets.QScrollArea):
                child.widget().setEnabled(not locked)
        self.load_preset_action.setEnabled(not locked)

    def start_detection(self) -> None:
        self._validate()
        if self._setup_errors or self._worker is not None:
            return
        input_path = self.input_field.path()
        output_path = self.output_path()
        file_paths = {key: field.path() for key, field in self.asset_fields.items()}
        ui_values = self.parameter_form.values()
        parameters = to_detection_parameters(ui_values)

        try:
            os.makedirs(output_path, exist_ok=True)
            with open(os.path.join(output_path, RUN_SETTINGS_FILE), "w", encoding="utf-8") as f:
                json.dump({
                    "application": APP_NAME,
                    "started": datetime.now().isoformat(timespec="seconds"),
                    "input_folder": input_path,
                    "image_count": len(self._image_paths),
                    "files": file_paths,
                    "parameters": ui_values,
                }, f, indent=2)
        except OSError as e:
            QtWidgets.QMessageBox.critical(self, "Cannot write to results folder", f"{output_path}\n\n{e}")
            return

        self._save_settings()
        self._run_output_path = output_path
        self._run_target_scale = float(ui_values["target_scale"])
        self.log_view.clear()
        self.stage_list.reset()
        self._current_stage = ""
        self.view_results_button.setEnabled(False)
        self._set_nav_done(PAGE_RUN, False)
        self._set_nav_done(PAGE_RESULTS, False)
        self._log(f"Started: {len(self._image_paths)} images from {input_path}")
        self._log(f"Results folder: {output_path}")

        self._worker = DetectionWorker(self._detect_controller, input_path, output_path, file_paths, parameters, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.error.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._run_started = time.monotonic()
        self._elapsed_timer.start()
        self.status_progress.setVisible(True)
        self._set_inputs_locked(True)
        self._update_run_controls()
        self._worker.start()

    def cancel_detection(self) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling…")
        self._log("Cancelling: finishing images already in progress…")

    def _on_progress(self, stage: str, completed: int, total: int) -> None:
        if self._worker is None:
            return
        if stage != self._current_stage:
            if self._current_stage:
                self._log(f"Finished: {self._current_stage}")
            self._log(f"{stage}…")
            self._current_stage = stage
        detail = f"{completed} / {total}" if total > 1 else ""
        self.stage_list.activate(stage, detail)
        for bar in (self.progress_bar, self.status_progress):
            if total == 0:
                bar.setRange(0, 0)
            else:
                bar.setRange(0, total)
                bar.setValue(completed)
        self._update_progress_label()

    def _update_progress_label(self) -> None:
        if self._worker is None:
            return
        elapsed = int(time.monotonic() - self._run_started)
        text = f"{self._current_stage or 'Starting'}  ·  {elapsed // 60}:{elapsed % 60:02d} elapsed"
        if self.progress_bar.maximum() > 1:
            text = f"{self._current_stage}: {self.progress_bar.value()} of {self.progress_bar.maximum()}  ·  {elapsed // 60}:{elapsed % 60:02d} elapsed"
        self.progress_label.setText(text)
        self.status_label.setText(text)

    def _on_finished(self, output: DetectionOutputData) -> None:
        if output.cancelled:
            self.stage_list.finish_active("cancelled")
            self._log("Cancelled. No results were saved.")
            self._end_run("Cancelled")
            return

        self.stage_list.activate(STAGES[-1])
        self.stage_list.finish_active("done")
        no_spot = sum(1 for row in output.results if float(row["spot_area"]) == 0)
        self._log(f"Finished in {self._elapsed_text()}: {len(output.results)} measured, "
                  f"{len(output.errors)} failed, {no_spot} without a detected spot.")
        for image_id, message in output.errors.items():
            self._log(f"  Failed {image_id}: {message}")
        self._set_nav_done(PAGE_RUN, True)
        self._show_results(output)
        self._end_run(f"Done: {len(output.results)} measured, {len(output.errors)} failed")
        self.view_results_button.setEnabled(True)
        self._go_to(PAGE_RESULTS)
        QtWidgets.QApplication.alert(self)

    def _on_failed(self, error_message: str) -> None:
        if self._worker is None:
            return
        self.stage_list.finish_active("error")
        lines = [line for line in error_message.strip().splitlines() if line.strip()]
        summary = lines[-1] if lines else "Unknown error"
        self._log(f"Error: {summary}")
        self._end_run("Detection failed")
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Critical)
        box.setWindowTitle("Detection failed")
        box.setText("Detection stopped because of an error.")
        box.setInformativeText(f"{summary}\n\nCheck that the model files are correct, "
                               "or see Help → Troubleshooting.")
        box.setDetailedText(error_message)
        box.exec_()

    def _end_run(self, status: str) -> None:
        self._elapsed_timer.stop()
        for bar in (self.progress_bar, self.status_progress):
            bar.setRange(0, 1)
            bar.setValue(1 if status.startswith("Done") else 0)
        self.status_progress.setVisible(False)
        self.progress_label.setText(f"{status}  ·  {self._elapsed_text()}")
        self.status_label.setText(status)
        self.cancel_button.setText("Cancel")
        self._set_inputs_locked(False)

    def _on_worker_finished(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()
        self._update_run_controls()
        self._validate()

    def _elapsed_text(self) -> str:
        elapsed = int(time.monotonic() - self._run_started)
        return f"{elapsed // 60}:{elapsed % 60:02d}"

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    # ------------------------------------------------------------------ results page

    def _show_results(self, output: DetectionOutputData) -> None:
        self._set_nav_done(PAGE_RESULTS, True)
        unit = "µm²" if self._run_target_scale == 1 else "px²"
        self.results_table.setSortingEnabled(False)
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.results_table.setHorizontalHeaderLabels(
            ["Image", "Status", f"Wing ({unit})", f"Spot ({unit})", "Ratio"]
        )
        header_tip = ("Areas are measured on the resized images. "
                      f"Multiply by (target scale)² = {self._run_target_scale ** 2:g} to convert px² to µm².")
        for column in (2, 3):
            item = self.results_table.horizontalHeaderItem(column)
            if item is not None:
                item.setToolTip(header_tip)

        rows: list[tuple[str, str, Optional[dict[str, str]], str]] = []
        for result in output.results:
            status = "No spot detected" if float(result["spot_area"]) == 0 else "Measured"
            rows.append((result["image_id"], status, result, ""))
        for image_id, message in output.errors.items():
            rows.append((image_id, "Failed", None, message))

        colors = {"Measured": style.OK, "No spot detected": style.WARN, "Failed": style.ERROR}
        self.results_table.setRowCount(len(rows))
        for row_index, (image_id, status, result, message) in enumerate(rows):
            id_item = QtWidgets.QTableWidgetItem(image_id)
            id_item.setData(QtCore.Qt.UserRole, message)
            self.results_table.setItem(row_index, 0, id_item)
            status_item = QtWidgets.QTableWidgetItem(status)
            status_item.setForeground(QtGui.QColor(colors[status]))
            if message:
                status_item.setToolTip(message)
            self.results_table.setItem(row_index, 1, status_item)
            if result is not None:
                for column, key, fmt in ((2, "wing_area", "{:,.0f}"), (3, "spot_area", "{:,.0f}"), (4, "spot_ratio", "{:.3f}")):
                    value = float(result[key])
                    item = NumericItem(fmt.format(value), value)
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    self.results_table.setItem(row_index, column, item)
        self.results_table.setSortingEnabled(True)
        self.results_table.sortItems(0)

        no_spot = sum(1 for _, status, _, _ in rows if status == "No spot detected")
        parts = [f"{len(output.results)} measured" + (f" ({no_spot} without a detected spot)" if no_spot else "")]
        if output.errors:
            parts.append(f"{len(output.errors)} failed")
        self.results_summary.setText(" · ".join(parts))

        has_output = os.path.isdir(output.output_path)
        self.open_folder_button.setEnabled(has_output)
        self.open_results_action.setEnabled(has_output)
        self.open_csv_button.setEnabled(os.path.isfile(os.path.join(output.output_path, RESULTS_CSV)))
        self.results_filter.setCurrentIndex(3 if output.errors and not output.results else 0)
        self._apply_results_filter()
        if self.results_table.rowCount():
            self.results_table.selectRow(0)

    def _apply_results_filter(self) -> None:
        wanted = self.results_filter.currentText()
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 1)
            status = status_item.text() if status_item else ""
            self.results_table.setRowHidden(row, wanted != "All images" and status != wanted)

    def _show_selected_result(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        id_item = self.results_table.item(row, 0)
        status_item = self.results_table.item(row, 1)
        if id_item is None or status_item is None:
            return
        image_id = id_item.text()
        self.preview_title.setText(image_id)
        message = id_item.data(QtCore.Qt.UserRole)
        if status_item.text() == "Failed":
            self.preview.show_message("No annotated image: this image could not be measured.")
            self.preview_detail.set_status("error", message or "Unknown error")
            return
        self.preview.set_image(os.path.join(self._run_output_path, f"{image_id}.png"))
        if status_item.text() == "No spot detected":
            self.preview_detail.set_status(
                "warn", "No spot larger than the minimum spot area was found. "
                        "If the wing has a spot, try a higher darkness threshold or a smaller minimum spot area.")
        else:
            self.preview_detail.set_status("", "")

    def _open_results_folder(self) -> None:
        if self._run_output_path:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self._run_output_path))

    def _open_results_csv(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.join(self._run_output_path, RESULTS_CSV)))

    # ------------------------------------------------------------------ settings and lifecycle

    def _restore_settings(self) -> None:
        geometry = self._settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.resize(1080, 780)

        for key, field in self.asset_fields.items():
            field.set_path(str(self._settings.value(f"assets/{key}", "")))
        if not all(field.path() for field in self.asset_fields.values()):
            for folder in default_asset_folders():
                for key, path in find_assets(folder).items():
                    if not self.asset_fields[key].path():
                        self.asset_fields[key].set_path(path)

        self.input_field.set_path(str(self._settings.value("paths/input", "")))
        self.output_field.set_path(str(self._settings.value("paths/output", "")))

        saved = self._settings.value("parameters", "")
        if saved:
            try:
                self.parameter_form.set_values(json.loads(str(saved)))
            except ValueError:
                pass
        self._on_parameters_changed()

    def _save_settings(self) -> None:
        self._settings.setValue("window/geometry", self.saveGeometry())
        for key, field in self.asset_fields.items():
            self._settings.setValue(f"assets/{key}", field.path())
        self._settings.setValue("paths/input", self.input_field.path())
        self._settings.setValue("paths/output", self.output_field.path())
        self._settings.setValue("parameters", json.dumps(self.parameter_form.values()))

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            "<p>Measures the area of wings and wing spots of <i>Drosophila suzukii</i> "
            "and other winged insects from microscopy images.</p>"
            f"<p><a href='{PROJECT_URL}'>{PROJECT_URL}</a></p>"
            "<p>Distributed under the MIT License.</p>",
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._worker is not None:
            answer = QtWidgets.QMessageBox.question(
                self, "Detection is running",
                "Detection is still running. Cancel it and quit?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self._worker.cancel()
            self._worker.wait()
        self._save_settings()
        super().closeEvent(event)


class NumericItem(QtWidgets.QTableWidgetItem):
    """Table item that shows formatted text but sorts by its numeric value."""

    def __init__(self, text: str, value: float):
        super().__init__(text)
        self._value = value

    def __lt__(self, other: QtWidgets.QTableWidgetItem) -> bool:
        if isinstance(other, NumericItem):
            return self._value < other._value
        return super().__lt__(other)
