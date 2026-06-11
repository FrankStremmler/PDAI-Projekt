import sys

from PySide6.QtWidgets import QApplication

from core.part_cloud.drive_gui import DriveCloudWidget, DriveItemsTableModel
from core.part_cloud.drive_controller import DriveController


def drive_main():
    app = QApplication(sys.argv)
    view = DriveCloudWidget()
    model = DriveItemsTableModel()
    controller = DriveController(view, model)
    view.set_qt_model(model)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    drive_main()

