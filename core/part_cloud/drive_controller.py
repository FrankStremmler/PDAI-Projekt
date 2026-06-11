from __future__ import annotations

import os
from typing import List

from PySide6.QtWidgets import QFileDialog, QMessageBox
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload




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
        if hasattr(self.view, "attach_controller"):
            self.view.attach_controller(self)

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

    def upload_files(self, file_paths: list[str]):
        if self.service is None:
            return

        successes = []
        failures = []

        for path in file_paths:
            if not os.path.exists(path):
                failures.append((path, "Datei existiert nicht"))
                continue

            if os.path.isdir(path):
                failures.append((path, "Ordner werden nicht unterstützt"))
                continue

            try:
                file_name = os.path.basename(path)
                media_body = MediaFileUpload(path, resumable=True)
                body = {
                    "name": file_name,
                    "parents": [self.current_folder_id],
                }
                self.service.files().create(body=body, media_body=media_body, fields="id, name").execute()
                successes.append(file_name)
            except Exception as e:
                failures.append((path, str(e)))

        self.refresh()

        if successes:
            QMessageBox.information(
                self.view,
                "Upload abgeschlossen",
                f"Hochgeladen:\n{chr(10).join(successes)}"
            )

        if failures:
            QMessageBox.warning(
                self.view,
                "Upload teilweise fehlgeschlagen",
                "\n".join([f"{path}: {reason}" for path, reason in failures])
            )

    def download_item(self, drive_item: DriveItem):
        if self.service is None:
            return

        if drive_item.is_folder:
            QMessageBox.information(self.view, "Download nicht möglich", "Ordner können nicht direkt heruntergeladen werden.")
            return

        default_name = drive_item.name or drive_item.id
        target_path, _ = QFileDialog.getSaveFileName(self.view, "Datei herunterladen", default_name)
        if not target_path:
            return

        try:
            if drive_item.mime_type.startswith("application/vnd.google-apps."):
                request = self.service.files().export(fileId=drive_item.id, mimeType="application/pdf")
            else:
                request = self.service.files().get_media(fileId=drive_item.id)

            with open(target_path, "wb") as file_handle:
                downloader = MediaIoBaseDownload(file_handle, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            QMessageBox.information(self.view, "Download abgeschlossen", f"Die Datei wurde gespeichert unter:\n{target_path}")
        except Exception as e:
            QMessageBox.warning(self.view, "Download fehlgeschlagen", f"Die Datei konnte nicht heruntergeladen werden:\n{e}")

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

