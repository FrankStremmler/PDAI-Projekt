from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFontDatabase
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QSpinBox, QPushButton, QColorDialog, QGroupBox, QDialogButtonBox,
    QTabWidget, QWidget, QComboBox, QMessageBox,
)

from standards_and_constants.view_constants import (
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_SECTION,
    FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_SIZE_DATETIME_DISPLAY,
    COLOR_CALENDAR_SIDEBAR_BG, COLOR_CALENDAR_SIDEBAR_TEXT,
    COLOR_CALENDAR_ACCENT, COLOR_DELETE_BUTTON_BG, FONT_FAMILY,
)
from standards_and_constants.config_manager import load_config, save_config


class SettingsDialog(QDialog):
    applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._create_fonts_tab(), "Schriftarten")
        tabs.addTab(self._create_colors_tab(), "Farben")
        layout.addWidget(tabs)

        self._preview_group = QGroupBox("Vorschau")
        preview_layout = QVBoxLayout(self._preview_group)
        self.preview_title = QLabel("Titelüberschrift")
        self.preview_subtitle = QLabel("Untertitel / Section")
        self.preview_body = QLabel("Dies ist ein normaler Fließtext zur Vorschau der Schriftgrößen.")
        self.preview_body.setWordWrap(True)
        self.preview_datetime = QLabel("17.06.2026 14:30")
        preview_layout.addWidget(self.preview_title)
        preview_layout.addWidget(self.preview_subtitle)
        preview_layout.addWidget(self.preview_body)
        preview_layout.addWidget(self.preview_datetime)
        layout.addWidget(self._preview_group)

        btn_layout = QHBoxLayout()
        self.btn_reset = QPushButton("Zurücksetzen")
        self.btn_reset.clicked.connect(self._reset_to_defaults)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Speichern")
        buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addLayout(btn_layout)

        self._load_settings()
        self._update_preview()

    def _create_spin_row(self, label: str, value: int, min_val=8, max_val=72) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        return spin

    def _create_fonts_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.combo_font_family = QComboBox()
        self.combo_font_family.setEditable(True)
        self.combo_font_family.addItems(QFontDatabase().families())
        idx = self.combo_font_family.findText(FONT_FAMILY)
        if idx >= 0:
            self.combo_font_family.setCurrentIndex(idx)
        form.addRow("Schriftart:", self.combo_font_family)

        self.spin_title = self._create_spin_row("Titel", FONT_SIZE_TITLE)
        self.spin_subtitle = self._create_spin_row("Untertitel", FONT_SIZE_SUBTITLE)
        self.spin_section = self._create_spin_row("Section", FONT_SIZE_SECTION)
        self.spin_body = self._create_spin_row("Fließtext", FONT_SIZE_BODY)
        self.spin_small = self._create_spin_row("Klein", FONT_SIZE_SMALL)
        self.spin_datetime = self._create_spin_row("Datumsanzeige", FONT_SIZE_DATETIME_DISPLAY, max_val=120)

        form.addRow("Titel:", self.spin_title)
        form.addRow("Untertitel:", self.spin_subtitle)
        form.addRow("Section:", self.spin_section)
        form.addRow("Fließtext:", self.spin_body)
        form.addRow("Klein:", self.spin_small)
        form.addRow("Datumsanzeige:", self.spin_datetime)

        self.combo_font_family.currentTextChanged.connect(self._update_preview)
        for spin in (self.spin_title, self.spin_subtitle, self.spin_section,
                     self.spin_body, self.spin_small, self.spin_datetime):
            spin.valueChanged.connect(self._update_preview)

        return tab

    def _color_button(self, color_hex: str) -> QPushButton:
        btn = QPushButton(color_hex)
        btn.setStyleSheet(
            f"background-color: {color_hex}; "
            f"color: {'white' if self._is_dark(color_hex) else 'black'}; "
            "padding: 4px 12px; border-radius: 4px;"
        )
        btn.setFixedWidth(120)
        return btn

    def _is_dark(self, hex_color: str) -> bool:
        color = QColor(hex_color)
        return color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114 < 128

    def _create_colors_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.btn_sidebar_bg = self._color_button(COLOR_CALENDAR_SIDEBAR_BG)
        self.btn_sidebar_text = self._color_button(COLOR_CALENDAR_SIDEBAR_TEXT)
        self.btn_accent = self._color_button(COLOR_CALENDAR_ACCENT)
        self.btn_delete_bg = self._color_button(COLOR_DELETE_BUTTON_BG)

        self.btn_sidebar_bg.clicked.connect(lambda: self._pick_color(self.btn_sidebar_bg))
        self.btn_sidebar_text.clicked.connect(lambda: self._pick_color(self.btn_sidebar_text))
        self.btn_accent.clicked.connect(lambda: self._pick_color(self.btn_accent))
        self.btn_delete_bg.clicked.connect(lambda: self._pick_color(self.btn_delete_bg))

        form.addRow("Sidebar-Hintergrund:", self.btn_sidebar_bg)
        form.addRow("Sidebar-Text:", self.btn_sidebar_text)
        form.addRow("Akzentfarbe:", self.btn_accent)
        form.addRow("Löschen-Button:", self.btn_delete_bg)

        return tab

    def _pick_color(self, button: QPushButton):
        current = QColor(button.text())
        color = QColorDialog.getColor(current, self, "Farbe auswählen")
        if color.isValid():
            hex_color = color.name()
            button.setText(hex_color)
            button.setStyleSheet(
                f"background-color: {hex_color}; "
                f"color: {'white' if self._is_dark(hex_color) else 'black'}; "
                "padding: 4px 12px; border-radius: 4px;"
            )

    def _reset_to_defaults(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Einstellungen zurücksetzen")
        msg.setText(
            "Dies löscht Ihre persönlichen Einstellungen und setzt diese auf ihre Startwerte zurück!"
        )
        msg.setInformativeText("Sollen die Einstellungen jetzt zurückgesetzt werden?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        if msg.exec() != QMessageBox.Yes:
            return

        ff = FONT_FAMILY
        idx = self.combo_font_family.findText(ff)
        if idx >= 0:
            self.combo_font_family.setCurrentIndex(idx)
        else:
            self.combo_font_family.setCurrentText(ff)

        self.spin_title.setValue(FONT_SIZE_TITLE)
        self.spin_subtitle.setValue(FONT_SIZE_SUBTITLE)
        self.spin_section.setValue(FONT_SIZE_SECTION)
        self.spin_body.setValue(FONT_SIZE_BODY)
        self.spin_small.setValue(FONT_SIZE_SMALL)
        self.spin_datetime.setValue(FONT_SIZE_DATETIME_DISPLAY)

        self.btn_sidebar_bg.setText(COLOR_CALENDAR_SIDEBAR_BG)
        self.btn_sidebar_text.setText(COLOR_CALENDAR_SIDEBAR_TEXT)
        self.btn_accent.setText(COLOR_CALENDAR_ACCENT)
        self.btn_delete_bg.setText(COLOR_DELETE_BUTTON_BG)

        for btn in (self.btn_sidebar_bg, self.btn_sidebar_text, self.btn_accent, self.btn_delete_bg):
            btn.setStyleSheet(
                f"background-color: {btn.text()}; "
                f"color: {'white' if self._is_dark(btn.text()) else 'black'}; "
                "padding: 4px 12px; border-radius: 4px;"
            )

        self._update_preview()

    def _update_preview(self):
        ff = self.combo_font_family.currentText()
        t = self.spin_title.value()
        st = self.spin_subtitle.value()
        sc = self.spin_section.value()
        b = self.spin_body.value()
        dt = self.spin_datetime.value()

        self.preview_title.setStyleSheet(f"font-size: {t}px; font-weight: bold; font-family: '{ff}';")
        self.preview_subtitle.setStyleSheet(f"font-size: {st}px; font-weight: bold; font-family: '{ff}';")
        self.preview_body.setStyleSheet(f"font-size: {b}px; font-family: '{ff}';")
        self.preview_datetime.setStyleSheet(f"font-size: {dt}px; font-weight: bold; font-family: '{ff}';")

    def _load_settings(self):
        cfg = load_config()
        v = cfg.get("view", {})

        ff = v.get("font_family", FONT_FAMILY)
        idx = self.combo_font_family.findText(ff)
        if idx >= 0:
            self.combo_font_family.setCurrentIndex(idx)

        font_cfg = v.get("font", {})
        self.spin_title.setValue(font_cfg.get("title", FONT_SIZE_TITLE))
        self.spin_subtitle.setValue(font_cfg.get("subtitle", FONT_SIZE_SUBTITLE))
        self.spin_section.setValue(font_cfg.get("section", FONT_SIZE_SECTION))
        self.spin_body.setValue(font_cfg.get("body", FONT_SIZE_BODY))
        self.spin_small.setValue(font_cfg.get("small", FONT_SIZE_SMALL))
        self.spin_datetime.setValue(font_cfg.get("datetime", FONT_SIZE_DATETIME_DISPLAY))

        color_cfg = v.get("color", {})
        self.btn_sidebar_bg.setText(color_cfg.get("sidebar_bg", COLOR_CALENDAR_SIDEBAR_BG))
        self.btn_sidebar_text.setText(color_cfg.get("sidebar_text", COLOR_CALENDAR_SIDEBAR_TEXT))
        self.btn_accent.setText(color_cfg.get("accent", COLOR_CALENDAR_ACCENT))
        self.btn_delete_bg.setText(color_cfg.get("delete_bg", COLOR_DELETE_BUTTON_BG))

    def _save_and_accept(self):
        cfg = load_config()
        cfg["view"] = {
            "font_family": self.combo_font_family.currentText(),
            "font": {
                "title": self.spin_title.value(),
                "subtitle": self.spin_subtitle.value(),
                "section": self.spin_section.value(),
                "body": self.spin_body.value(),
                "small": self.spin_small.value(),
                "datetime": self.spin_datetime.value(),
            },
            "color": {
                "sidebar_bg": self.btn_sidebar_bg.text(),
                "sidebar_text": self.btn_sidebar_text.text(),
                "accent": self.btn_accent.text(),
                "delete_bg": self.btn_delete_bg.text(),
            },
        }
        save_config(cfg)

        self.applied.emit()
        self.accept()
