from .hb_config_model import ConfigManager


def apply_global_theme(q_app):
    colors = ConfigManager().config.theme

    stylesheet = f"""
        QMainWindow, QDialog {{
            background-color: {colors.background};
            color: {colors.text};
        }}

        QWidget {{
            color: {colors.text};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10px;
        }}

        QPushButton {{
            background-color: {colors.accent};
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }}

        QPushButton:hover {{
            background-color: {colors.accent}cc;
        }}

        QTableWidget, QTableView {{
            background-color: {colors.surface};
            gridline-color: {colors.background};
            border: 1px solid {colors.surface};
        }}

        QHeaderView::section {{
            background-color: {colors.background};
            color: {colors.text};
            padding: 4px;
            border: none;
        }}
    """
    q_app.setStyleSheet(stylesheet)
