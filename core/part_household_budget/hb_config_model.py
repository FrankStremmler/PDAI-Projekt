import json
import os
from pydantic import BaseModel, Field


class ThemeColors(BaseModel):
    background: str = "#1e1e1e"
    surface: str = "#2d2d2d"
    text: str = "#ffffff"
    accent: str = "#2563eb"

    def update(self, background: str = None, surface: str = None, text: str = None, accent: str = None):
        if background is not None:
            self.background = background
        if surface is not None:
            self.surface = surface
        if text is not None:
            self.text = text
        if accent is not None:
            self.accent = accent


class AppConfig(BaseModel):
    ai_provider: str = Field("gemini", description="Ausgewählter KI-Anbieter (gemini, openai)")
    current_theme: str = Field("dark", description="Aktuelles Farbschema-Name")
    theme: ThemeColors = Field(default_factory=ThemeColors)


class ConfigManager:
    _instance = None
    CONFIG_FILE = "config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        cfg_path = self._get_config_path()
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    self.config = AppConfig.model_validate_json(f.read())
            except Exception:
                self.config = AppConfig()
        else:
            self.config = AppConfig()
            self.save_config()

    def save_config(self):
        cfg_path = self._get_config_path()
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(self.config.model_dump_json(indent=4))

    def _get_config_path(self):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.CONFIG_FILE)

    def set_theme(self, theme_name: str):
        self.config.current_theme = theme_name
        if theme_name == "dark":
            self.config.theme = ThemeColors(background="#1e1e1e", surface="#2d2d2d", text="#ffffff", accent="#2563eb")
        elif theme_name == "light":
            self.config.theme = ThemeColors(background="#f8fafc", surface="#ffffff", text="#0f172a", accent="#3b82f6")
        self.save_config()

    def update_colors(self, background: str = None, surface: str = None, text: str = None):
        self.config.theme.update(background=background, surface=surface, text=text)
        self.save_config()
