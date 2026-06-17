from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStyle,
    QSizePolicy,
)
from PySide6.QtGui import QIcon
from standards_and_constants.view_constants import (
    SIDEBAR_ICON_SIZE,
    SIDEBAR_EXPANDED_WIDTH,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_SPACING,
    SIDEBAR_ANIMATION_DURATION,
    WINDOW_TITLE,
    WINDOW_INITIAL_WIDTH,
    WINDOW_INITIAL_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_RESIZE_THRESHOLD_RATIO,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_INITIAL_WIDTH, WINDOW_INITIAL_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._initial_width = WINDOW_INITIAL_WIDTH
        self.expanded_width = SIDEBAR_EXPANDED_WIDTH
        self.collapsed_width = SIDEBAR_COLLAPSED_WIDTH
        self.sidebar_collapsed = False

        central = QWidget()
        self.setCentralWidget(central)

        # Sidebar wrapper with toggle icon
        self.side_panel = QWidget()
        self.side_panel.setMaximumWidth(self.expanded_width)
        self.side_panel.setMinimumWidth(self.expanded_width)
        self.side_panel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)

        self.sidebar = QListWidget()
        self.sidebar.setIconSize(SIDEBAR_ICON_SIZE)
        self.sidebar.setSelectionMode(QListWidget.SingleSelection)
        self.sidebar.setUniformItemSizes(True)
        self.sidebar.setSpacing(SIDEBAR_SPACING)
        self.sidebar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        side_layout = QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)
        side_layout.addWidget(self.sidebar, 1)

        self.exit_item = None
        self.settings_item = None
        self._last_app_row = None

        # Main area where sub-apps are shown
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Layout
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.side_panel)
        h.addWidget(self.stack, 1)

        self._animation = QPropertyAnimation(self.side_panel, b"maximumWidth", self)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setDuration(SIDEBAR_ANIMATION_DURATION)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        threshold = int(self._initial_width * WINDOW_RESIZE_THRESHOLD_RATIO)
        if self.width() <= threshold and not self.sidebar_collapsed:
            self.set_sidebar_collapsed(True, animate=True)
        elif self.width() > threshold and self.sidebar_collapsed:
            self.set_sidebar_collapsed(False, animate=True)

    def add_app(self, name: str, widget: QWidget, icon=None, entry_id: str | None = None):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, entry_id or name)
        item.setData(Qt.UserRole + 1, name)
        if icon is not None:
            if isinstance(icon, QIcon):
                item.setIcon(icon)
            else:
                item.setIcon(self.style().standardIcon(icon))
        item.setToolTip(name)
        self.sidebar.addItem(item)
        self.stack.addWidget(widget)

    def add_collapse_item(self, name: str, icon: QIcon | None = None):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, "collapse")
        item.setData(Qt.UserRole + 1, name)
        if icon is not None:
            item.setIcon(icon)
        item.setToolTip(name)
        self.sidebar.addItem(item)

    def add_spacer(self, height: int):
        item = QListWidgetItem("")
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(1, height))
        self.sidebar.addItem(item)

    def add_settings_item(self, name: str, icon: QIcon | None = None):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, "settings")
        item.setData(Qt.UserRole + 1, name)
        if icon is not None:
            item.setIcon(icon)
        item.setToolTip(name)
        self.sidebar.addItem(item)
        self.settings_item = item

    def add_exit_item(self, name: str, icon: QIcon | None = None):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, "exit")
        item.setData(Qt.UserRole + 1, name)
        if icon is not None:
            item.setIcon(icon)
        item.setToolTip(name)
        self.sidebar.addItem(item)
        self.exit_item = item

    def set_current_index(self, index: int):
        if 0 <= index < self.sidebar.count():
            item = self.sidebar.item(index)
            role = item.data(Qt.UserRole)
            if role in ("collapse", "settings", "exit", None):
                return
            app_index = self._stack_index_for_row(index)
            if app_index is None:
                return
            self.sidebar.setCurrentRow(index)
            self.stack.setCurrentIndex(app_index)
            self._last_app_row = index

    def _stack_index_for_row(self, row: int):
        app_rows = []
        for r in range(self.sidebar.count()):
            item = self.sidebar.item(r)
            role = item.data(Qt.UserRole)
            if role not in ("collapse", "settings", "exit", None):
                app_rows.append(r)
        if row in app_rows:
            return app_rows.index(row)
        return None

    def set_sidebar_collapsed(self, collapsed: bool, animate: bool = True):
        self.sidebar_collapsed = collapsed
        target_width = self.collapsed_width if collapsed else self.expanded_width
        self.side_panel.setMinimumWidth(target_width)
        if animate:
            self._animation.stop()
            self._animation.setStartValue(self.side_panel.width())
            self._animation.setEndValue(target_width)
            self._animation.start()
        else:
            self.side_panel.setFixedWidth(target_width)

        for index in range(self.sidebar.count()):
            item = self.sidebar.item(index)
            role = item.data(Qt.UserRole)
            if role is None:
                continue
            display_name = item.data(Qt.UserRole + 1)
            item.setText(display_name if not collapsed else "")

    def toggle_sidebar(self):
        self.set_sidebar_collapsed(not self.sidebar_collapsed)

    def restore_last_app_selection(self):
        if self._last_app_row is not None:
            self.sidebar.setCurrentRow(self._last_app_row)
