from PySide6.QtCore import QSize

from standards_and_constants.config_manager import load_config


# ---------------------------------------------------------------------------
# Sidebar (pdai_gui/views.py)
# ---------------------------------------------------------------------------
SIDEBAR_ICON_SIZE = QSize(28, 28)
SIDEBAR_EXPANDED_WIDTH = 200
SIDEBAR_COLLAPSED_WIDTH = 70
SIDEBAR_SPACING = 4
SIDEBAR_ANIMATION_DURATION = 250

# ---------------------------------------------------------------------------
# Font family
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"


# ---------------------------------------------------------------------------
# Main window (pdai_gui/views.py)
# ---------------------------------------------------------------------------
WINDOW_TITLE = "PDAI — Startseite"
WINDOW_INITIAL_WIDTH = 1000
WINDOW_INITIAL_HEIGHT = 600
WINDOW_MIN_WIDTH = 500
WINDOW_MIN_HEIGHT = 300
WINDOW_RESIZE_THRESHOLD_RATIO = 0.75

# ---------------------------------------------------------------------------
# Font sizes
# ---------------------------------------------------------------------------
FONT_SIZE_TITLE = 16
FONT_SIZE_SUBTITLE = 13
FONT_SIZE_SECTION = 14
FONT_SIZE_BODY = 10
FONT_SIZE_SMALL = 8
FONT_SIZE_DATETIME_DISPLAY = 38

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLOR_DELETE_BUTTON_BG = "#c62828"
COLOR_DELETE_BUTTON_TEXT = "white"
COLOR_CALENDAR_SIDEBAR_BG = "#202124"
COLOR_CALENDAR_SIDEBAR_TEXT = "white"
COLOR_CALENDAR_SIDEBAR_SECONDARY = "#9aa0a6"
COLOR_CALENDAR_ACCENT = "#1a73e8"
COLOR_CALENDAR_TILE_BG = "#f1f3f4"
COLOR_CALENDAR_TILE_HOVER_BG = "#e8eaed"
COLOR_CALENDAR_TILE_TEXT = "#202124"
COLOR_BOOKED = "green"
COLOR_PENDING = "yellow"
COLOR_SUSPICIOUS = "red"
COLOR_NEGATIVE_AMOUNT = "red"
COLOR_POSITIVE_AMOUNT = "darkGreen"

# ---------------------------------------------------------------------------
# Common style strings
# ---------------------------------------------------------------------------
STYLE_TITLE_BOLD = f"font-size: {FONT_SIZE_TITLE}px; font-weight: bold;"
STYLE_SUBTITLE_BOLD = f"font-size: {FONT_SIZE_SUBTITLE}px; font-weight: bold;"
STYLE_SECTION_BOLD = f"font-size: {FONT_SIZE_SECTION}px; font-weight: bold;"
STYLE_DATETIME_DISPLAY = f"font-size: {FONT_SIZE_DATETIME_DISPLAY}px; font-weight: bold;"
STYLE_GROUPBOX = "QGroupBox { font-weight: bold; margin-top: 10px; }"
STYLE_DELETE_BUTTON = (
    f"color: {COLOR_DELETE_BUTTON_TEXT}; "
    f"background-color: {COLOR_DELETE_BUTTON_BG}; "
    "padding: 6px 12px; border-radius: 4px;"
)

# ---------------------------------------------------------------------------
# Calendar widget (cal_gui.py)
# ---------------------------------------------------------------------------
CALENDAR_SIDEBAR_WIDTH = 220
CALENDAR_WINDOW_WIDTH = 900
CALENDAR_WINDOW_HEIGHT = 550
CALENDAR_SIDEBAR_STYLE = (
    f"background-color: {COLOR_CALENDAR_SIDEBAR_BG}; "
    f"color: {COLOR_CALENDAR_SIDEBAR_TEXT};"
)
CALENDAR_ACCOUNT_LABEL_STYLE = (
    f"color: {COLOR_CALENDAR_SIDEBAR_SECONDARY}; "
    f"padding: 10px; font-weight: bold; font-size: {FONT_SIZE_SECTION}px;"
    f"background-color: {COLOR_CALENDAR_SIDEBAR_BG};"
)
CALENDAR_NAV_BUTTON_STYLE = (
    "text-align: left; padding: 10px; background: none; "
    f"border: none; color: white; font-size: {FONT_SIZE_BODY}px;")
CALENDAR_SECTION_LABEL_STYLE = (
    f"color: {COLOR_CALENDAR_SIDEBAR_SECONDARY}; "
    "padding: 10px 10px 20px 10px; "
    f"font-size: {FONT_SIZE_SMALL}px; text-transform: uppercase;"
)
CALENDAR_LIST_STYLE = "background: transparent; border: none; color: white; padding-left: 5px;"
CALENDAR_CREATE_EVENT_BUTTON_STYLE = (
    "margin: 0 10px 10px 10px; padding: 8px; font-weight: bold;"
)
CALENDAR_TILE_BUTTON_STYLE = (
    "QPushButton {"
    "  text-align: left;"
    "  padding: 15px;"
    f"  font-size: {FONT_SIZE_BODY*1.2}px;"
    "  font-weight: bold;"
    f"  color: {COLOR_CALENDAR_TILE_TEXT};"
    f"  background-color: {COLOR_CALENDAR_TILE_BG};"
    "  border: none;"
    "  border-left: 6px solid %s;"
    "  border-radius: 4px;"
    "}"
    "QPushButton:hover {"
    f"  background-color: {COLOR_CALENDAR_TILE_HOVER_BG};"
    "}"
)
CALENDAR_NEW_EVENT_BUTTON_STYLE = (
    f"padding: 10px; background-color: {COLOR_CALENDAR_ACCENT}; "
    "color: white; border-radius: 4px;"
)
CALENDAR_DATETIME_FORMAT = "dd-MM-yyyy HH:mm"

# ---------------------------------------------------------------------------
# Contact / Calendar shared dialog constants
# ---------------------------------------------------------------------------
DIALOG_MIN_WIDTH = 380

# ---------------------------------------------------------------------------
# Contact view (contact_view.py)
# ---------------------------------------------------------------------------
SEARCH_PLACEHOLDER = "Suche (Name, E-Mail, Telefon, Adresse)"

# ---------------------------------------------------------------------------
# Date/time display format
# ---------------------------------------------------------------------------
DATETIME_DISPLAY_FORMAT = "dd.MM.yyyy hh:mm"

# ---------------------------------------------------------------------------
# Household budget review dialogs
# ---------------------------------------------------------------------------
RECEIPT_DIALOG_MIN_WIDTH = 700
RECEIPT_DIALOG_MIN_HEIGHT = 500
STATEMENT_DIALOG_MIN_WIDTH = 800
STATEMENT_DIALOG_MIN_HEIGHT = 600
