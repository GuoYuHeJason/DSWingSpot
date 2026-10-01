import os
from typing import Any, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from app import style
from app.parameters import (
    OVERDETECTION_METHOD_KEY, OVERDETECTION_METHODS, PARAMETER_GROUPS,
    ParameterSpec, default_parameters,
)


def clean_path(text: str) -> str:
    """
    Normalises a path typed or pasted by the user:
    strips spaces and surrounding quotes, expands ~ and normalises separators.
    """
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    if text.startswith("file://"):
        text = QtCore.QUrl(text).toLocalFile()
    if not text:
        return ""
    return os.path.normpath(os.path.expanduser(text))


class Card(QtWidgets.QFrame):
    """White panel with a title, optional description and a body layout."""

    def __init__(self, title: str, subtitle: str = "", parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(10)

        header = QtWidgets.QHBoxLayout()
        text = QtWidgets.QVBoxLayout()
        text.setSpacing(2)
        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("cardTitle")
        text.addWidget(title_label)
        if subtitle:
            subtitle_label = QtWidgets.QLabel(subtitle)
            subtitle_label.setObjectName("cardSubtitle")
            subtitle_label.setWordWrap(True)
            text.addWidget(subtitle_label)
        header.addLayout(text, 1)
        self.header_actions = QtWidgets.QHBoxLayout()
        header.addLayout(self.header_actions)
        layout.addLayout(header)

        self.body = QtWidgets.QVBoxLayout()
        self.body.setSpacing(12)
        layout.addLayout(self.body)


class StatusLabel(QtWidgets.QLabel):
    """Small coloured message shown under an input."""

    GLYPHS = {"ok": "✓", "warn": "⚠", "error": "✕", "info": "ℹ"}

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.set_status("", "")

    def set_status(self, level: str, message: str) -> None:
        if not message:
            self.clear()
            self.setVisible(False)
            return
        self.setVisible(True)
        color = style.STATUS_COLORS.get(level, style.MUTED)
        self.setText(f"{self.GLYPHS.get(level, '')}  {message}")
        self.setStyleSheet(f"color: {color};")


class PathField(QtWidgets.QWidget):
    """Labelled path input with a Browse button, drag and drop support and a validation message."""

    changed = QtCore.pyqtSignal(str)

    def __init__(
        self,
        label: str,
        select_directory: bool,
        file_filter: str = "",
        placeholder: str = "",
        tooltip: str = "",
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent)
        self._select_directory = select_directory
        self._file_filter = file_filter
        self.setAcceptDrops(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.label = QtWidgets.QLabel(label)
        self.label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.label)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        self.line_edit = QtWidgets.QLineEdit()
        self.line_edit.setPlaceholderText(placeholder or ("Choose a folder…" if select_directory else "Choose a file…"))
        self.line_edit.setAcceptDrops(False)
        self.line_edit.setClearButtonEnabled(True)
        row.addWidget(self.line_edit, 1)
        self.browse_button = QtWidgets.QPushButton("Browse…")
        self.browse_button.clicked.connect(self.browse)
        row.addWidget(self.browse_button)
        layout.addLayout(row)

        self.status = StatusLabel()
        layout.addWidget(self.status)

        if tooltip:
            self.label.setToolTip(tooltip)
            self.line_edit.setToolTip(tooltip)

        # validate after typing pauses rather than on every keystroke
        self._debounce = QtCore.QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(lambda: self.changed.emit(self.path()))
        self.line_edit.textChanged.connect(lambda _: self._debounce.start())

    def path(self) -> str:
        return clean_path(self.line_edit.text())

    def set_path(self, path: str) -> None:
        self.line_edit.setText(path)
        self._debounce.stop()
        self.changed.emit(self.path())

    def set_placeholder(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    def set_status(self, level: str, message: str) -> None:
        self.status.set_status(level, message)
        self.line_edit.setProperty("status", level if level in ("warn", "error") else "")
        self.line_edit.style().unpolish(self.line_edit)
        self.line_edit.style().polish(self.line_edit)

    def _start_directory(self) -> str:
        current = self.path()
        if current and os.path.isdir(current):
            return current
        if current and os.path.isdir(os.path.dirname(current)):
            return os.path.dirname(current)
        return os.path.expanduser("~")

    def browse(self) -> None:
        if self._select_directory:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, self.label.text(), self._start_directory())
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, self.label.text(), self._start_directory(), f"{self._file_filter};;All files (*)"
            )
        if path:
            self.set_path(os.path.normpath(path))

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        path = event.mimeData().urls()[0].toLocalFile()
        if self._select_directory and os.path.isfile(path):
            path = os.path.dirname(path)
        self.set_path(os.path.normpath(path))
        event.acceptProposedAction()


class _NoWheelFilter(QtCore.QObject):
    """Stops scrolling the parameter page from accidentally changing spin box values."""

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Wheel and isinstance(obj, QtWidgets.QWidget) and not obj.hasFocus():
            # hand the scroll to the parent so the page still scrolls
            parent = obj.parentWidget()
            if parent is not None:
                QtCore.QCoreApplication.sendEvent(parent, event)
            return True
        return False


class ParameterForm(QtWidgets.QWidget):
    """Grouped, typed editors for all detection parameters."""

    changed = QtCore.pyqtSignal()
    # shared so editors line up and have equal widths across groups
    LABEL_WIDTH = 300
    EDITOR_WIDTH = 190

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._editors: dict[str, QtWidgets.QWidget] = {}
        self._labels: dict[str, QtWidgets.QLabel] = {}
        self._specs: dict[str, ParameterSpec] = {}
        self._defaults = default_parameters()
        self._wheel_filter = _NoWheelFilter(self)
        self._advanced_cards: list[Card] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        for group in PARAMETER_GROUPS:
            card = Card(group.title, group.description)
            form = QtWidgets.QFormLayout()
            form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldsStayAtSizeHint)
            form.setHorizontalSpacing(24)
            form.setVerticalSpacing(10)
            for spec in group.parameters:
                self._add_parameter(form, spec)
                if spec.key == "adjust_bin_thresh":
                    self._add_method_selector(form)
            card.body.addLayout(form)
            if group.advanced:
                if not self._advanced_cards:
                    # advanced groups are listed last, hidden behind a toggle
                    self.advanced_toggle = QtWidgets.QPushButton("Show advanced parameters")
                    self.advanced_toggle.setObjectName("linkButton")
                    self.advanced_toggle.setCheckable(True)
                    self.advanced_toggle.toggled.connect(self._set_advanced_visible)
                    layout.addWidget(self.advanced_toggle, 0, QtCore.Qt.AlignLeft)
                self._advanced_cards.append(card)
                card.setVisible(False)
            layout.addWidget(card)
        layout.addStretch(1)

        self._update_enabled_state()

    def _add_parameter(self, form: QtWidgets.QFormLayout, spec: ParameterSpec) -> None:
        editor: QtWidgets.QWidget
        if spec.kind == "bool":
            editor = QtWidgets.QCheckBox()
            editor.toggled.connect(self._on_changed)
        else:
            if spec.kind == "int":
                editor = QtWidgets.QSpinBox()
                editor.setRange(int(spec.minimum), int(spec.maximum))
                editor.setSingleStep(int(spec.step))
            else:
                editor = QtWidgets.QDoubleSpinBox()
                editor.setDecimals(spec.decimals)
                editor.setRange(spec.minimum, spec.maximum)
                editor.setSingleStep(spec.step)
            editor.setKeyboardTracking(False)
            editor.setGroupSeparatorShown(abs(spec.maximum) >= 10_000)
            editor.setFixedWidth(self.EDITOR_WIDTH)
            editor.setAlignment(QtCore.Qt.AlignRight)
            if spec.unit:
                editor.setSuffix(f"  {spec.unit}")
            editor.setFocusPolicy(QtCore.Qt.StrongFocus)
            editor.installEventFilter(self._wheel_filter)
            editor.valueChanged.connect(self._on_changed)
        label = QtWidgets.QLabel(spec.label)
        label.setMinimumWidth(self.LABEL_WIDTH)
        tooltip = f"{spec.tooltip}\n\nDefault: {self._format_value(spec, spec.default)}   (key: {spec.key})"
        label.setToolTip(tooltip)
        editor.setToolTip(tooltip)
        self._editors[spec.key] = editor
        self._labels[spec.key] = label
        self._specs[spec.key] = spec
        self._set_editor_value(spec.key, spec.default)
        form.addRow(label, editor)

    def _add_method_selector(self, form: QtWidgets.QFormLayout) -> None:
        combo = QtWidgets.QComboBox()
        for key, text in OVERDETECTION_METHODS.items():
            combo.addItem(text, key)
        combo.setMinimumWidth(self.EDITOR_WIDTH)
        combo.installEventFilter(self._wheel_filter)
        combo.setFocusPolicy(QtCore.Qt.StrongFocus)
        tooltip = "Which reference height decides whether a spot is over-detected. Only the selected method's value is used."
        combo.setToolTip(tooltip)
        combo.currentIndexChanged.connect(self._on_changed)
        label = QtWidgets.QLabel("Reference height")
        label.setMinimumWidth(self.LABEL_WIDTH)
        label.setToolTip(tooltip)
        self._editors[OVERDETECTION_METHOD_KEY] = combo
        self._labels[OVERDETECTION_METHOD_KEY] = label
        form.addRow(label, combo)

    @staticmethod
    def _format_value(spec: ParameterSpec, value: Any) -> str:
        if spec.kind == "bool":
            return "on" if value else "off"
        text = f"{value:g}" if isinstance(value, float) else str(value)
        return f"{text} {spec.unit}".strip()

    def _set_advanced_visible(self, visible: bool) -> None:
        for card in self._advanced_cards:
            card.setVisible(visible)
        self.advanced_toggle.setText("Hide advanced parameters" if visible else "Show advanced parameters")

    def _set_editor_value(self, key: str, value: Any) -> None:
        editor = self._editors[key]
        editor.blockSignals(True)
        try:
            if isinstance(editor, QtWidgets.QCheckBox):
                if isinstance(value, str):
                    value = value.strip().lower() in {"1", "true", "t", "yes", "y"}
                editor.setChecked(bool(value))
            elif isinstance(editor, QtWidgets.QSpinBox):
                editor.setValue(int(float(value)))
            elif isinstance(editor, QtWidgets.QDoubleSpinBox):
                editor.setValue(float(value))
            elif isinstance(editor, QtWidgets.QComboBox):
                index = editor.findData(value)
                if index >= 0:
                    editor.setCurrentIndex(index)
        finally:
            editor.blockSignals(False)

    def values(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, editor in self._editors.items():
            if isinstance(editor, QtWidgets.QCheckBox):
                result[key] = editor.isChecked()
            elif isinstance(editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                result[key] = editor.value()
            elif isinstance(editor, QtWidgets.QComboBox):
                result[key] = editor.currentData()
        return result

    def set_values(self, values: dict[str, Any]) -> list[str]:
        """Sets known parameters and returns the keys that were not recognised."""
        unknown = []
        for key, value in values.items():
            if key not in self._editors:
                unknown.append(key)
                continue
            try:
                self._set_editor_value(key, value)
            except (TypeError, ValueError):
                unknown.append(key)
        self._on_changed()
        return unknown

    def restore_defaults(self) -> None:
        self.set_values(self._defaults)

    def modified_count(self) -> int:
        values = self.values()
        return sum(1 for key in self._editors if values[key] != self._defaults[key])

    def _on_changed(self, *_: Any) -> None:
        # keep median blur kernel odd, as required by OpenCV
        blur = self._editors["median_blur_ksize"]
        if isinstance(blur, QtWidgets.QSpinBox) and blur.value() % 2 == 0:
            blur.setValue(blur.value() + 1)
            return
        self._update_enabled_state()
        values = self.values()
        for key, label in self._labels.items():
            label.setProperty("modified", values[key] != self._defaults[key])
            label.style().unpolish(label)
            label.style().polish(label)
        self.changed.emit()

    def _update_enabled_state(self) -> None:
        adjust = self._editors["adjust_bin_thresh"]
        enabled = isinstance(adjust, QtWidgets.QCheckBox) and adjust.isChecked()
        method = self._editors[OVERDETECTION_METHOD_KEY]
        selected = method.currentData() if isinstance(method, QtWidgets.QComboBox) else None
        for key in [OVERDETECTION_METHOD_KEY, "adjust_rate", *OVERDETECTION_METHODS]:
            active = enabled and (key not in OVERDETECTION_METHODS or key == selected)
            self._editors[key].setEnabled(active)
            self._labels[key].setEnabled(active)
        otsu = self._editors["ostu_threshold"]
        use_otsu = isinstance(otsu, QtWidgets.QCheckBox) and otsu.isChecked()
        self._editors["bin_thresh"].setEnabled(not use_otsu)
        self._labels["bin_thresh"].setEnabled(not use_otsu)


class ThumbnailStrip(QtWidgets.QListWidget):
    """Horizontal strip of image previews, loaded incrementally to keep the UI responsive."""

    MAX_THUMBNAILS = 30
    ICON_SIZE = QtCore.QSize(96, 72)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setObjectName("thumbnails")
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setWrapping(False)
        self.setMovement(QtWidgets.QListView.Static)
        self.setIconSize(self.ICON_SIZE)
        self.setSpacing(4)
        self.setFixedHeight(self.ICON_SIZE.height() + 44)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self._pending: list[str] = []
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._load_next)

    def set_images(self, paths: list[str]) -> None:
        self.clear()
        self._pending = list(paths[: self.MAX_THUMBNAILS])
        for path in self._pending:
            item = QtWidgets.QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            item.setSizeHint(QtCore.QSize(self.ICON_SIZE.width() + 12, self.ICON_SIZE.height() + 30))
            self.addItem(item)
        self._next_index = 0
        self._timer.start()

    def _load_next(self) -> None:
        if self._next_index >= len(self._pending):
            self._timer.stop()
            return
        path = self._pending[self._next_index]
        reader = QtGui.QImageReader(path)
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid():
            reader.setScaledSize(size.scaled(self.ICON_SIZE, QtCore.Qt.KeepAspectRatio))
        image = reader.read()
        item = self.item(self._next_index)
        if item is not None and not image.isNull():
            item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(image)))
        self._next_index += 1


class StageList(QtWidgets.QWidget):
    """Vertical list of pipeline stages with their state."""

    STATES = {
        "pending": ("○", "#a0aab4"),
        "active": ("●", style.ACCENT),
        "done": ("✓", style.OK),
        "error": ("✕", style.ERROR),
        "cancelled": ("–", style.WARN),
    }

    def __init__(self, stages: list[str], parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._stages = stages
        self._icons: dict[str, QtWidgets.QLabel] = {}
        self._labels: dict[str, QtWidgets.QLabel] = {}
        self._details: dict[str, QtWidgets.QLabel] = {}
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(6)
        for row, stage in enumerate(stages):
            icon = QtWidgets.QLabel()
            icon.setFixedWidth(16)
            icon.setAlignment(QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(stage)
            detail = QtWidgets.QLabel()
            detail.setObjectName("hint")
            detail.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            layout.addWidget(icon, row, 0)
            layout.addWidget(label, row, 1)
            layout.addWidget(detail, row, 2)
            self._icons[stage], self._labels[stage], self._details[stage] = icon, label, detail
        layout.setColumnStretch(1, 1)
        self.reset()

    def reset(self) -> None:
        for stage in self._stages:
            self.set_state(stage, "pending")
            self._details[stage].clear()

    def set_state(self, stage: str, state: str, detail: Optional[str] = None) -> None:
        if stage not in self._icons:
            return
        glyph, color = self.STATES[state]
        self._icons[stage].setText(glyph)
        self._icons[stage].setStyleSheet(f"color: {color}; font-weight: 700;")
        self._labels[stage].setStyleSheet("font-weight: 600;" if state == "active" else
                                          ("color: #a0aab4;" if state == "pending" else ""))
        if detail is not None:
            self._details[stage].setText(detail)

    def activate(self, stage: str, detail: str = "") -> None:
        """Marks all earlier stages done and this stage active."""
        if stage not in self._stages:
            return
        index = self._stages.index(stage)
        for earlier in self._stages[:index]:
            if self._icons[earlier].text() in (self.STATES["pending"][0], self.STATES["active"][0]):
                self.set_state(earlier, "done")
        self.set_state(stage, "active", detail)

    def finish_active(self, state: str) -> None:
        for stage in self._stages:
            if self._icons[stage].text() == self.STATES["active"][0]:
                self.set_state(stage, state)


class ImagePreview(QtWidgets.QLabel):
    """Shows an image scaled to fit while keeping its aspect ratio."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._pixmap: Optional[QtGui.QPixmap] = None
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(240, 180)
        self.setWordWrap(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setStyleSheet(f"background: #eef1f4; border-radius: 6px; color: {style.MUTED}; padding: 12px;")

    def set_image(self, path: str) -> bool:
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            self.show_message("Preview not available")
            return False
        self._pixmap = pixmap
        self._rescale()
        return True

    def show_message(self, text: str) -> None:
        self._pixmap = None
        self.setPixmap(QtGui.QPixmap())
        self.setText(text)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._pixmap is None:
            return
        size = self.contentsRect().size()
        self.setPixmap(self._pixmap.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
