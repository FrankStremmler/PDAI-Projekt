from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDialogButtonBox, QLabel, QPushButton, QColorDialog
)
from PySide6.QtCore import Qt
from .hb_config_model import ConfigManager
from standards_and_constants.hb_prompts_constants import PROVIDER_GEMINI, PROVIDER_OPENAI


class ColorPickerButton(QPushButton):
    def __init__(self, initial_color: str, label: str, parent=None):
        super().__init__(parent)
        self.label = label
        self._color = initial_color
        self.setFixedSize(80, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _pick_color(self):
        qcolor = QColorDialog.getColor(self._color, self, f"{self.label} auswählen")
        if qcolor.isValid():
            self._color = qcolor.name()
            self._update_style()

    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #888888;
                border-radius: 4px;
            }}
        """)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._update_style()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(450)

        self.config_manager = ConfigManager()
        current_config = self.config_manager.config

        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.combo_provider = QComboBox()
        self.combo_provider.addItems([PROVIDER_GEMINI.capitalize(), PROVIDER_OPENAI.capitalize()])
        index = self.combo_provider.findText(current_config.ai_provider.capitalize())
        if index >= 0:
            self.combo_provider.setCurrentIndex(index)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark", "Light"])
        index = self.combo_theme.findText(current_config.current_theme.capitalize())
        if index >= 0:
            self.combo_theme.setCurrentIndex(index)
        self.combo_theme.currentTextChanged.connect(self._on_theme_changed)

        self.form_layout.addRow(QLabel("KI-Dienstleister:"), self.combo_provider)
        self.form_layout.addRow(QLabel("Farbschema:"), self.combo_theme)

        self.form_layout.addRow(QLabel(""))
        self.form_layout.addRow(QLabel("<b>Farben</b>"))

        self.btn_bg = ColorPickerButton(current_config.theme.background, "Hintergrundfarbe")
        self.form_layout.addRow(QLabel("Hintergrundfarbe:"), self.btn_bg)

        self.btn_text = ColorPickerButton(current_config.theme.text, "Textfarbe")
        self.form_layout.addRow(QLabel("Textfarbe:"), self.btn_text)

        self.btn_box_bg = ColorPickerButton(current_config.theme.surface, "Box-Hintergrundfarbe")
        self.form_layout.addRow(QLabel("Box-Hintergrundfarbe:"), self.btn_box_bg)

        self.main_layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

    def _on_theme_changed(self, theme_name: str):
        theme_name = theme_name.lower()
        if theme_name == "dark":
            self.btn_bg.set_color("#1e1e1e")
            self.btn_text.set_color("#ffffff")
            self.btn_box_bg.set_color("#2d2d2d")
        elif theme_name == "light":
            self.btn_bg.set_color("#f8fafc")
            self.btn_text.set_color("#0f172a")
            self.btn_box_bg.set_color("#ffffff")

    def get_selected_settings(self) -> dict:
        return {
            "ai_provider": self.combo_provider.currentText().lower(),
            "theme": self.combo_theme.currentText().lower(),
            "background": self.btn_bg.get_color(),
            "text": self.btn_text.get_color(),
            "box_bg": self.btn_box_bg.get_color(),
        }
