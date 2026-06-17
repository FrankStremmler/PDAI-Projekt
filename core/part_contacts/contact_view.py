from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QHBoxLayout,
    QTableView,
    QLineEdit,
)
from standards_and_constants.view_constants import SEARCH_PLACEHOLDER



class ContactAppView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kontakte")

        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar_layout = QVBoxLayout()
        self.account_label = QLabel("")
        self.group_list_widget = QListWidget()

        sidebar_layout.addWidget(self.account_label)
        sidebar_layout.addWidget(self.group_list_widget, 1)

        main_layout.addLayout(sidebar_layout, 1)

        # Content area
        content_layout = QVBoxLayout()
        self.current_group_title = QLabel("")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(SEARCH_PLACEHOLDER)

        self.sort_button = QPushButton("A-Z")
        self.sort_button.setCheckable(True)


        self.create_contact_button = QPushButton("Kontakt erstellen")

        content_layout.addWidget(self.current_group_title)
        content_layout.addWidget(self.search_input)
        content_layout.addWidget(self.sort_button)
        content_layout.addWidget(self.create_contact_button)

        self.content_stack = QStackedWidget()


        # Page 0 placeholder (dashboard)
        page0 = QWidget()
        page0_layout = QVBoxLayout(page0)
        page0_layout.addWidget(QLabel("Bitte Gruppe auswählen"))
        self.content_stack.addWidget(page0)

        # Page 1 table
        page1 = QWidget()
        page1_layout = QVBoxLayout(page1)
        self.table_view = QTableView()
        page1_layout.addWidget(self.table_view, 1)
        self.content_stack.addWidget(page1)

        content_layout.addWidget(self.content_stack, 1)
        main_layout.addLayout(content_layout, 2)

        # Initial state
        self.create_contact_button.setVisible(False)
        self.content_stack.setCurrentIndex(0)

    def set_qt_model(self, model):
        self.table_view.setModel(model)

