import json
import os


_CONFIG_FILE = "config.json"


def _get_config_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "core",
        _CONFIG_FILE,
    )


_DEFAULT_CONFIG = {
    "view": {
        "font_family": "Segoe UI",
        "font": {
            "title": 20,
            "subtitle": 16,
            "section": 18,
            "body": 14,
            "small": 11,
            "datetime": 48,
        },
        "color": {
            "sidebar_bg": "#202124",
            "sidebar_text": "#ffffff",
            "accent": "#1a73e8",
            "delete_bg": "#c62828",
        },
    },
    "ai_provider": "openai",
    "current_theme": "dark",
    "theme": {
        "background": "#1e1e1e",
        "surface": "#2d2d2d",
        "text": "#ffffff",
        "accent": "#2563eb",
    },
}


def load_config() -> dict:
    path = _get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = _DEFAULT_CONFIG.copy()
            merged.update(cfg)
            return merged
        except Exception:
            return dict(_DEFAULT_CONFIG)
    return dict(_DEFAULT_CONFIG)


def save_config(config: dict):
    path = _get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
