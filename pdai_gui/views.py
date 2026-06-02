from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDAI — Startseite")
        self.resize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setSelectionMode(QListWidget.SingleSelection)

        # Main area where sub-apps are shown
        self.stack = QStackedWidget()

        # Layout
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.sidebar)
        h.addWidget(self.stack, 1)

    def add_app(self, name: str, widget: QWidget, icon_id: QStyle.StandardPixmap = None):
        item = QListWidgetItem(name)
        if icon_id is not None:
            icon = self.style().standardIcon(icon_id)
            item.setIcon(icon)
        self.sidebar.addItem(item)
        self.stack.addWidget(widget)

    def set_current_index(self, index: int):
        if 0 <= index < self.stack.count():
            self.sidebar.setCurrentRow(index)
            self.stack.setCurrentIndex(index)
