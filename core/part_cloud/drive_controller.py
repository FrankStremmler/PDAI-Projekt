from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QMessageBox




from providers.google_parts import google_base

from .drive_model import DriveItem


class DriveController:
    def __init__(self, view, qt_model):
        self.view = view
        self.qt_model = qt_model
        self.service = None  # googleapiclient discovery resource



        self.current_folder_id = "root"
        self.current_items: List[DriveItem] = []

        self._init_service_and_bind()

    def _init_service_and_bind(self):
        try:
            self.service = google_base.create_service("drive")
        except Exception as e:
            QMessageBox.critical(self.view, "Google Drive Fehler", f"Konnte Google Drive Service nicht erstellen:\n{e}")
            return

        # UI wiring
        if hasattr(self.view, "refresh_button"):
            self.view.refresh_button.clicked.connect(self.refresh)
        if hasattr(self.view, "back_button"):
            self.view.back_button.clicked.connect(self.go_back)
        if hasattr(self.view, "create_folder_button"):
            self.view.create_folder_button.clicked.connect(self.create_folder)

        # list item click
        if hasattr(self.view, "items_list_widget"):
            self.view.items_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.refresh()

    def refresh(self):
        if self.service is None:
            return


        try:
            items = self.list_children(self.current_folder_id)
            self.current_items = items
            self.qt_model.set_items(items)

            # Label soll den Anzeigenamen des Ordners anzeigen (falls möglich)
            if self.current_folder_id == "root":
                folder_name = "Root"
            else:
                folder_name = self._get_folder_name(self.current_folder_id) or self.current_folder_id

            if hasattr(self.view, "current_folder_label"):
                self.view.current_folder_label.setText(f"Ordner: {folder_name}")

        except Exception as e:
            QMessageBox.warning(self.view, "Laden fehlgeschlagen", f"Konnte Inhalte nicht laden:\n{e}")

    def _get_folder_name(self, folder_id: str) -> str:
        try:
            metadata = self.service.files().get(fileId=folder_id, fields="name").execute()
            return metadata.get("name", "")
        except Exception:
            return ""

    def list_children(self, folder_id: str) -> List[DriveItem]:
        # Folders + files, non-trashed
        query = f"'{folder_id}' in parents and trashed = false"

        results = (
            self.service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=200,
            )
            .execute()
        )
        items = results.get("files", [])

        drive_items: List[DriveItem] = []
        for it in items:
            is_folder = it.get("mimeType") == "application/vnd.google-apps.folder"
            drive_items.append(
                DriveItem(
                    id=it["id"],
                    name=it["name"],
                    mime_type=it.get("mimeType", ""),
                    is_folder=is_folder,
                )
            )

        # Sort folders first, then by name
        drive_items.sort(key=lambda x: (not x.is_folder, (x.name or "").lower()))
        return drive_items

    def on_item_double_clicked(self, item_widget_item):
        drive_item: DriveItem = item_widget_item.data(256)
        if not drive_item:
            return

        if drive_item.is_folder:
            self.current_folder_id = drive_item.id
            self.refresh()

    def go_back(self):
        # Simplified: just go to root if no path tracking exists.
        # (Path tracking can be added later.)
        self.current_folder_id = "root"
        self.refresh()

    def create_folder(self):
        service = self.service
        if service is None:
            return


        folder_name = "Neuer Ordner"
        try:
            # Let user set a name via input dialog on the view if available
            if hasattr(self.view, "prompt_folder_name"):
                folder_name = self.view.prompt_folder_name()

            folder_body = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.current_folder_id],
            }

            created = self.service.files().create(body=folder_body, fields="id, name, mimeType").execute()
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self.view, "Erstellen fehlgeschlagen", f"Ordner konnte nicht erstellt werden:\n{e}")

