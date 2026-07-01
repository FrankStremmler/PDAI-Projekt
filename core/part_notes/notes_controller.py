from __future__ import annotations

import datetime
import io
import json
import os
from typing import List, Optional

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QMessageBox

from providers.google_parts import google_base

from .notes_gui import NotesListView
from .notes_model import Note, NoteType


PRIVATE_NOTES_FOLDER = "Private_Notes"


class NotesController:
    def __init__(self, view: NotesListView):
        self.view = view
        self.service = None
        self.folder_id: Optional[str] = None

        self._init_service()

    def _init_service(self):
        try:
            self.service = google_base.create_service("drive")
        except Exception as e:
            QMessageBox.critical(
                self.view,
                "Drive Fehler",
                f"Konnte Google Drive Service nicht erstellen:\n{e}",
            )
            return
        self._ensure_private_notes_folder()
        self.refresh()

    def _ensure_private_notes_folder(self):
        if self.service is None:
            return
        try:
            query = (
                f"name='{PRIVATE_NOTES_FOLDER}' and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"'root' in parents and trashed=false"
            )
            results = (
                self.service.files()
                .list(q=query, fields="files(id, name)", pageSize=10)
                .execute()
            )
            files = results.get("files", [])
            if files:
                self.folder_id = files[0]["id"]
            else:
                folder_body = {
                    "name": PRIVATE_NOTES_FOLDER,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                created = (
                    self.service.files()
                    .create(body=folder_body, fields="id, name")
                    .execute()
                )
                self.folder_id = created["id"]
        except Exception as e:
            QMessageBox.warning(
                self.view,
                "Ordner Fehler",
                f"Konnte Ordner '{PRIVATE_NOTES_FOLDER}' nicht anlegen/suchen:\n{e}",
            )

    # ── Refresh / list ──

    def refresh(self):
        if self.service is None or self.folder_id is None:
            return
        try:
            notes = self._list_notes()
            notes.sort(key=lambda n: n.updated_at or "", reverse=True)
            self.view.refresh_list(notes)
        except Exception as e:
            QMessageBox.warning(
                self.view,
                "Laden fehlgeschlagen",
                f"Konnte Notizen nicht laden:\n{e}",
            )

    def _list_notes(self) -> List[Note]:
        query = f"'{self.folder_id}' in parents and trashed=false"
        results = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, appProperties, modifiedTime)",
                pageSize=200,
            )
            .execute()
        )
        items = results.get("files", [])
        notes: List[Note] = []
        for item in items:
            note = self._build_note_from_file(item)
            if note is not None:
                notes.append(note)
        return notes

    @staticmethod
    def _infer_note_type(name: str, mime_type: str, app_props: dict) -> Optional[NoteType]:
        if app_props and "note_type" in app_props:
            try:
                return NoteType(app_props["note_type"])
            except ValueError:
                pass

        if mime_type and mime_type.startswith("image/"):
            return NoteType.IMAGE
        if mime_type == "application/json":
            return NoteType.CHECKLIST
        if mime_type == "text/plain":
            return NoteType.PLAIN_TEXT

        ext = os.path.splitext(name)[1].lower()
        if ext == ".txt":
            return NoteType.PLAIN_TEXT
        if ext == ".json":
            return NoteType.CHECKLIST
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
            return NoteType.IMAGE
        return None

    def _build_note_from_file(self, file_data: dict) -> Optional[Note]:
        file_id = file_data.get("id", "")
        name = file_data.get("name", "")
        mime_type = file_data.get("mimeType", "")
        app_props = file_data.get("appProperties") or {}
        modified_time = file_data.get("modifiedTime", "")

        note_type = self._infer_note_type(name, mime_type, app_props)
        if note_type is None:
            return None

        title = os.path.splitext(name)[0]
        created_at = app_props.get("created_at", modified_time)
        updated_at = app_props.get("updated_at", modified_time)
        image_file_id = file_id if note_type == NoteType.IMAGE else None

        return Note(
            id=file_id,
            title=title,
            note_type=note_type,
            content="",
            created_at=created_at,
            updated_at=updated_at,
            image_file_id=image_file_id,
        )

    # ── Load full note content (for editor) ──

    def load_note_content(self, note: Note) -> Note:
        if self.service is None:
            return note
        if note.note_type in (NoteType.PLAIN_TEXT, NoteType.CHECKLIST):
            mime_type = "text/plain" if note.note_type == NoteType.PLAIN_TEXT else "application/json"
            content = self._download_content(note.id, mime_type)
            if content is not None:
                note.content = content
        return note

    def _download_content(self, file_id: str, mime_type: str) -> Optional[str]:
        try:
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return content
        except Exception:
            return None

    # ── Create (and return note) ──

    def create_note_and_return(self, note_type: NoteType, image_path: Optional[str] = None) -> Optional[Note]:
        if self.service is None or self.folder_id is None:
            return None

        now = datetime.datetime.now().isoformat()
        title = "Neue Notiz"
        note = None

        if note_type == NoteType.IMAGE and image_path:
            ext = os.path.splitext(image_path)[1]
            file_name = f"{title}{ext}"
            media = MediaFileUpload(image_path, resumable=True)
            body = {
                "name": file_name,
                "parents": [self.folder_id],
                "appProperties": {
                    "note_type": note_type.value,
                    "created_at": now,
                    "updated_at": now,
                },
            }
            try:
                created = (
                    self.service.files()
                    .create(body=body, media_body=media, fields="id, name, appProperties")
                    .execute()
                )
                note = Note(
                    id=created["id"],
                    title=title,
                    note_type=NoteType.IMAGE,
                    content="",
                    created_at=now,
                    updated_at=now,
                    image_file_id=created["id"],
                )
            except Exception as e:
                QMessageBox.warning(self.view, "Fehler", f"Bild konnte nicht hochgeladen werden:\n{e}")
                return None

        elif note_type == NoteType.PLAIN_TEXT:
            file_name = f"{title}.txt"
            body = {
                "name": file_name,
                "parents": [self.folder_id],
                "mimeType": "text/plain",
                "appProperties": {
                    "note_type": note_type.value,
                    "created_at": now,
                    "updated_at": now,
                },
            }
            media = MediaIoBaseUpload(io.BytesIO(b""), mimetype="text/plain", resumable=True)
            created = (
                self.service.files()
                .create(body=body, media_body=media, fields="id")
                .execute()
            )
            note = Note(
                id=created["id"],
                title=title,
                note_type=NoteType.PLAIN_TEXT,
                content="",
                created_at=now,
                updated_at=now,
            )

        elif note_type == NoteType.CHECKLIST:
            file_name = f"{title}.json"
            init_content = json.dumps([], ensure_ascii=False).encode("utf-8")
            body = {
                "name": file_name,
                "parents": [self.folder_id],
                "mimeType": "application/json",
                "appProperties": {
                    "note_type": note_type.value,
                    "created_at": now,
                    "updated_at": now,
                },
            }
            media = MediaIoBaseUpload(io.BytesIO(init_content), mimetype="application/json", resumable=True)
            created = (
                self.service.files()
                .create(body=body, media_body=media, fields="id")
                .execute()
            )
            note = Note(
                id=created["id"],
                title=title,
                note_type=NoteType.CHECKLIST,
                content="[]",
                created_at=now,
                updated_at=now,
            )

        self.refresh()
        return note

    # ── Save ──

    def save_note(self, note: Note):
        if self.service is None:
            return
        now = datetime.datetime.now().isoformat()
        note.updated_at = now

        if note.note_type == NoteType.PLAIN_TEXT:
            file_name = f"{note.title}.txt"
            content_bytes = note.content.encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(content_bytes), mimetype="text/plain", resumable=True)
            body = {
                "name": file_name,
                "mimeType": "text/plain",
                "appProperties": {
                    "note_type": note.note_type.value,
                    "created_at": note.created_at,
                    "updated_at": now,
                },
            }
            self.service.files().update(
                fileId=note.id, body=body, media_body=media, fields="id, name, appProperties"
            ).execute()

        elif note.note_type == NoteType.CHECKLIST:
            file_name = f"{note.title}.json"
            content_bytes = note.content.encode("utf-8")
            media = MediaIoBaseUpload(io.BytesIO(content_bytes), mimetype="application/json", resumable=True)
            body = {
                "name": file_name,
                "mimeType": "application/json",
                "appProperties": {
                    "note_type": note.note_type.value,
                    "created_at": note.created_at,
                    "updated_at": now,
                },
            }
            self.service.files().update(
                fileId=note.id, body=body, media_body=media, fields="id, name, appProperties"
            ).execute()

        elif note.note_type == NoteType.IMAGE:
            body = {
                "appProperties": {
                    "note_type": note.note_type.value,
                    "created_at": note.created_at,
                    "updated_at": now,
                },
            }
            self.service.files().update(
                fileId=note.id, body=body, fields="appProperties"
            ).execute()

        self.refresh()

    # ── Delete (trash) ──

    def delete_note(self, note: Note):
        if self.service is None:
            return
        try:
            self.service.files().update(
                fileId=note.id, body={"trashed": True}, fields="id"
            ).execute()
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self.view, "Löschen fehlgeschlagen", f"Notiz konnte nicht gelöscht werden:\n{e}")

    # ── Image display ──

    def load_image_into_label(self, note: Note, label: QLabel):
        if self.service is None or not note.image_file_id:
            label.setText("(Kein Bild verfügbar)")
            return

        try:
            request = self.service.files().get_media(fileId=note.image_file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            file_stream.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(file_stream.read())
            if pixmap.isNull():
                label.setText("(Bild konnte nicht geladen werden)")
                return

            max_size = 600
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(
                    max_size,
                    max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            label.setPixmap(pixmap)
        except Exception as e:
            label.setText(f"(Fehler: {e})")
