from __future__ import annotations

import json
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .notes_model import ChecklistItem, Note, NoteType
from standards_and_constants.view_constants import STYLE_DELETE_BUTTON

# ── help ──

TYPE_ICONS = {
    NoteType.PLAIN_TEXT: "📝",
    NoteType.CHECKLIST: "☑️",
    NoteType.IMAGE: "🖼️",
}

TYPE_LABELS = {
    NoteType.PLAIN_TEXT: "Text",
    NoteType.CHECKLIST: "Liste",
    NoteType.IMAGE: "Bild",
}


def _short_preview(note: Note, max_len: int = 80) -> str:
    if note.note_type == NoteType.CHECKLIST and note.content:
        try:
            items = json.loads(note.content)
            done = sum(1 for i in items if i.get("checked"))
            return f"{done}/{len(items)} erledigt"
        except Exception:
            pass
    text = note.content or ""
    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return text


# ── Card widget ──

class NoteCard(QFrame):
    clicked = Signal(object)

    def __init__(self, note: Note, parent=None):
        super().__init__(parent)
        self._note = note
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._style_card())
        self.setFixedHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.icon_label = QLabel(TYPE_ICONS.get(note.note_type, "📄"))
        self.icon_label.setFont(QFont("Segoe UI", 22))
        self.icon_label.setFixedWidth(40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        self.title_label = QLabel(note.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        self.title_label.setFont(title_font)
        text_layout.addWidget(self.title_label)

        preview = _short_preview(note)
        self.preview_label = QLabel(preview if preview else "(leer)")
        self.preview_label.setStyleSheet("color: #888;")
        self.preview_label.setWordWrap(True)
        text_layout.addWidget(self.preview_label)

        layout.addLayout(text_layout, 1)

        meta_layout = QVBoxLayout()
        self.type_label = QLabel(TYPE_LABELS.get(note.note_type, ""))
        self.type_label.setStyleSheet(
            "color: #666; font-size: 10px; background: #eee; "
            "padding: 2px 6px; border-radius: 4px;"
        )
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        meta_layout.addWidget(self.type_label)

        updated = note.updated_at or ""
        if len(updated) > 10:
            updated = updated[:10]
        self.date_label = QLabel(updated)
        self.date_label.setStyleSheet("color: #999; font-size: 9px;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        meta_layout.addWidget(self.date_label)
        meta_layout.addStretch(1)

        layout.addLayout(meta_layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self._note)
        super().mousePressEvent(event)

    @staticmethod
    def _style_card() -> str:
        return (
            "QFrame {"
            "  background: #2d2d2d; border: 1px solid #444;"
            "  border-radius: 6px; margin: 2px 0;"
            "}"
            "QFrame:hover {"
            "  background: #3a3a3a; border: 1px solid #2563eb;"
            "}"
        )


# ── Note list view (card grid) ──

class NoteListView(QWidget):
    note_selected = Signal(object)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(4, 4, 4, 4)
        self.card_layout.setSpacing(6)
        self.card_layout.addStretch(1)
        self.scroll.setWidget(self.card_container)

        layout.addWidget(self.scroll)

        self._notes: List[Note] = []
        self._card_widgets: List[NoteCard] = []

    def set_notes(self, notes: List[Note]):
        self._notes = notes or []
        self._rebuild_cards()

    def _rebuild_cards(self):
        for w in self._card_widgets:
            w.deleteLater()
        self._card_widgets.clear()

        for item in self.card_layout.findChildren(NoteCard):
            item.deleteLater()

        for i in reversed(range(self.card_layout.count())):
            w = self.card_layout.itemAt(i)
            if w and w.widget() and isinstance(w.widget(), NoteCard):
                w.widget().deleteLater()

        self._card_widgets = []
        for note in self._notes:
            card = NoteCard(note)
            card.clicked.connect(self._on_card_clicked)
            self.card_layout.insertWidget(self.card_layout.count() - 1, card)
            self._card_widgets.append(card)

    def _on_card_clicked(self, note: Note):
        self.note_selected.emit(note)


# ── Note editor (detail view) ──

class NoteEditor(QWidget):
    save_requested = Signal(object)
    delete_requested = Signal(object)
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self._note: Optional[Note] = None
        self._has_unsaved = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Top bar
        top_bar = QHBoxLayout()
        self.back_button = QPushButton("← Zurück")
        self.delete_button = QPushButton("Löschen")
        self.delete_button.setStyleSheet(STYLE_DELETE_BUTTON)
        self.save_button = QPushButton("Speichern")
        self.save_button.setEnabled(False)

        top_bar.addWidget(self.back_button)
        top_bar.addStretch(1)
        top_bar.addWidget(self.delete_button)
        top_bar.addWidget(self.save_button)
        root.addLayout(top_bar)

        # Title
        title_layout = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Notiz-Titel")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.title_edit.setFont(title_font)
        title_layout.addWidget(self.title_edit, 1)
        root.addLayout(title_layout)

        # Content editor stack
        self.editor_stack = QStackedWidget()

        # Page 0 – plain text
        page_text = QWidget()
        text_layout = QVBoxLayout(page_text)
        text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Notiztext eingeben…")
        text_layout.addWidget(self.text_edit)
        self.editor_stack.addWidget(page_text)

        # Page 1 – checklist
        page_cl = QWidget()
        cl_layout = QVBoxLayout(page_cl)
        cl_layout.setContentsMargins(0, 0, 0, 0)

        self.cl_open_label = QLabel("Offen")
        self.cl_open_label.setStyleSheet("font-weight: bold; color: #aaa; padding: 4px 0;")
        cl_layout.addWidget(self.cl_open_label)

        self.cl_open_list = QListWidget()
        self.cl_open_list.setAlternatingRowColors(True)
        cl_layout.addWidget(self.cl_open_list, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #555;")
        cl_layout.addWidget(sep)

        self.cl_done_label = QLabel("Erledigt")
        self.cl_done_label.setStyleSheet("font-weight: bold; color: #aaa; padding: 4px 0;")
        cl_layout.addWidget(self.cl_done_label)

        self.cl_done_list = QListWidget()
        self.cl_done_list.setAlternatingRowColors(True)
        cl_layout.addWidget(self.cl_done_list, 1)

        cl_btn_bar = QHBoxLayout()
        self.cl_add_btn = QPushButton("+ Item")
        self.cl_remove_btn = QPushButton("− Item")
        cl_btn_bar.addWidget(self.cl_add_btn)
        cl_btn_bar.addWidget(self.cl_remove_btn)
        cl_btn_bar.addStretch(1)
        cl_layout.addLayout(cl_btn_bar)
        self.editor_stack.addWidget(page_cl)

        # Page 2 – image
        page_img = QWidget()
        img_layout = QVBoxLayout(page_img)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        self.image_label = QLabel("(Kein Bild geladen)")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #888;")
        img_scroll.setWidget(self.image_label)
        img_layout.addWidget(img_scroll, 1)

        self.image_desc_edit = QTextEdit()
        self.image_desc_edit.setMaximumHeight(100)
        self.image_desc_edit.setPlaceholderText("Beschreibung (optional)")
        img_layout.addWidget(self.image_desc_edit)
        self.editor_stack.addWidget(page_img)

        root.addWidget(self.editor_stack, 1)

        # Signals
        self.back_button.clicked.connect(self.back_requested)
        self.save_button.clicked.connect(self._on_save)
        self.delete_button.clicked.connect(self._on_delete)
        self.title_edit.textChanged.connect(self._mark_unsaved)
        self.text_edit.textChanged.connect(self._mark_unsaved)
        self.cl_open_list.itemChanged.connect(self._on_cl_item_changed)
        self.cl_open_list.itemDoubleClicked.connect(self._on_cl_item_double_clicked)
        self.cl_done_list.itemChanged.connect(self._on_cl_item_changed)
        self.cl_done_list.itemDoubleClicked.connect(self._on_cl_item_double_clicked)
        self.cl_add_btn.clicked.connect(self._on_cl_add)
        self.cl_remove_btn.clicked.connect(self._on_cl_remove)
        self.image_desc_edit.textChanged.connect(self._mark_unsaved)

    # ── public ──

    def load_note(self, note: Note):
        self._note = note
        self._has_unsaved = False
        self.save_button.setEnabled(False)

        self.title_edit.blockSignals(True)
        self.title_edit.setText(note.title)
        self.title_edit.blockSignals(False)

        if note.note_type == NoteType.PLAIN_TEXT:
            self.editor_stack.setCurrentIndex(0)
            self.text_edit.blockSignals(True)
            self.text_edit.setPlainText(note.content)
            self.text_edit.blockSignals(False)

        elif note.note_type == NoteType.CHECKLIST:
            self.editor_stack.setCurrentIndex(1)
            self._populate_cl(note.content)

        elif note.note_type == NoteType.IMAGE:
            self.editor_stack.setCurrentIndex(2)
            self.image_label.setText("(Bild wird geladen…)")
            self.image_desc_edit.blockSignals(True)
            self.image_desc_edit.setPlainText(note.content)
            self.image_desc_edit.blockSignals(False)

    def get_note(self) -> Optional[Note]:
        if self._note is None:
            return None
        note = self._note
        note.title = self.title_edit.text().strip() or note.title

        if note.note_type == NoteType.PLAIN_TEXT:
            note.content = self.text_edit.toPlainText()
        elif note.note_type == NoteType.CHECKLIST:
            items = []
            for lst in (self.cl_open_list, self.cl_done_list):
                for i in range(lst.count()):
                    item = lst.item(i)
                    items.append(
                        ChecklistItem(
                            text=item.text(),
                            checked=item.checkState() == Qt.CheckState.Checked,
                        )
                    )
            note.content = json.dumps(
                [m.model_dump() for m in items], ensure_ascii=False
            )
        elif note.note_type == NoteType.IMAGE:
            note.content = self.image_desc_edit.toPlainText()

        return note

    def set_image_pixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            max_size = 600
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(
                    max_size,
                    max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("(Bild konnte nicht geladen werden)")

    # ── internal ──

    def _populate_cl(self, content: str):
        self._cl_block_all(True)
        self.cl_open_list.clear()
        self.cl_done_list.clear()
        if content:
            try:
                items_data = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                items_data = []
            for item_data in items_data:
                ci = ChecklistItem(**item_data) if isinstance(item_data, dict) else ChecklistItem(text=str(item_data))
                self._add_cl_item(ci.text, ci.checked, block_signals=True)
        self._cl_block_all(False)

    def _cl_block_all(self, blocked: bool):
        self.cl_open_list.blockSignals(blocked)
        self.cl_done_list.blockSignals(blocked)

    def _add_cl_item(self, text: str, checked: bool = False, block_signals: bool = False):
        item = QListWidgetItem(text)
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEditable
        )
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self._apply_cl_item_style(item)
        target = self.cl_done_list if checked else self.cl_open_list
        if block_signals:
            target.blockSignals(True)
        target.addItem(item)
        if block_signals:
            target.blockSignals(False)

    @staticmethod
    def _apply_cl_item_style(item: QListWidgetItem):
        font = item.font()
        font.setStrikeOut(item.checkState() == Qt.CheckState.Checked)
        item.setFont(font)

    def _on_cl_item_changed(self, item: QListWidgetItem):
        self._apply_cl_item_style(item)

        source = self.cl_open_list if item.listWidget() is self.cl_open_list else self.cl_done_list
        is_now_checked = item.checkState() == Qt.CheckState.Checked
        belongs_to_open = source is self.cl_open_list

        if belongs_to_open and is_now_checked:
            self._move_item(item, source, self.cl_done_list)
        elif not belongs_to_open and not is_now_checked:
            self._move_item(item, source, self.cl_open_list)

        self._mark_unsaved()

    def _move_item(self, item: QListWidgetItem, source: QListWidget, target: QListWidget):
        row = source.row(item)
        taken = source.takeItem(row)
        if taken is None:
            return
        target.blockSignals(True)
        target.addItem(taken)
        target.blockSignals(False)

    def _on_cl_item_double_clicked(self, item: QListWidgetItem):
        item.listWidget().editItem(item)

    def _on_cl_add(self):
        self._add_cl_item("Neuer Eintrag")
        last_row = self.cl_open_list.count() - 1
        self.cl_open_list.editItem(self.cl_open_list.item(last_row))
        self._mark_unsaved()

    def _on_cl_remove(self):
        for lst in (self.cl_open_list, self.cl_done_list):
            row = lst.currentRow()
            if row >= 0:
                lst.takeItem(row)
                self._mark_unsaved()
                return

    def _on_save(self):
        self.save_requested.emit(self.get_note())

    def _on_delete(self):
        if self._note:
            self.delete_requested.emit(self._note)

    def _mark_unsaved(self):
        if self._note is not None:
            self._has_unsaved = True
            self.save_button.setEnabled(True)


# ── Main notes view (list + editor stacked) ──

class NotesListView(QWidget):
    def __init__(self):
        super().__init__()
        self._controller = None
        self._current_note: Optional[Note] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        self.new_note_button = QPushButton("+ Neue Notiz")
        self.new_note_button.setMenu(self._build_new_menu())
        self.refresh_button = QPushButton("↻ Aktualisieren")
        toolbar.addWidget(self.new_note_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        # Stack: list ↔ editor
        self.stack = QStackedWidget()

        self.note_list = NoteListView()
        self.note_list.note_selected.connect(self._on_note_selected)
        self.stack.addWidget(self.note_list)

        self.editor = NoteEditor()
        self.editor.back_requested.connect(self._on_back_to_list)
        self.editor.save_requested.connect(self._on_save_note)
        self.editor.delete_requested.connect(self._on_delete_note)
        self.stack.addWidget(self.editor)

        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack, 1)

        # Signals
        self.refresh_button.clicked.connect(self._on_refresh)

    def _build_new_menu(self) -> QMenu:
        menu = QMenu(self)
        a_text = menu.addAction("📝 Text-Notiz")
        a_cl = menu.addAction("☑️ Checkliste")
        a_img = menu.addAction("🖼️ Bild-Notiz")
        a_text.triggered.connect(lambda: self._on_new_note(NoteType.PLAIN_TEXT))
        a_cl.triggered.connect(lambda: self._on_new_note(NoteType.CHECKLIST))
        a_img.triggered.connect(lambda: self._on_new_note(NoteType.IMAGE))
        return menu

    def attach_controller(self, controller):
        self._controller = controller

    def set_qt_model(self, model):
        self.note_list.set_notes(getattr(model, "_notes", []))

    def refresh_list(self, notes: List[Note]):
        self.note_list.set_notes(notes)

    # ── internal ──

    def _on_new_note(self, note_type: NoteType):
        if not self._controller:
            return

        image_path = None
        if note_type == NoteType.IMAGE:
            path, _ = QFileDialog.getOpenFileName(
                self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
            )
            if not path:
                return
            image_path = path

        note = self._controller.create_note_and_return(note_type, image_path)
        if note:
            self._current_note = note
            self.editor.load_note(note)
            self.stack.setCurrentIndex(1)
            if note_type == NoteType.IMAGE and note.image_file_id:
                self._controller.load_image_into_label(note, self.editor.image_label)

    def _on_note_selected(self, note: Note):
        if not self._controller:
            return
        self._current_note = note
        note_with_content = self._controller.load_note_content(note)
        self.editor.load_note(note_with_content)
        self.stack.setCurrentIndex(1)

        if note.note_type == NoteType.IMAGE and note.image_file_id:
            self._controller.load_image_into_label(note, self.editor.image_label)

    def _on_back_to_list(self):
        if self._has_unsaved():
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Möchten Sie die Änderungen verwerfen?",
                QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return
        self.stack.setCurrentIndex(0)
        if self._controller:
            self._controller.refresh()

    def _has_unsaved(self) -> bool:
        return self.editor.save_button.isEnabled()

    def _on_save_note(self, note: Note):
        if not self._controller:
            return
        self._controller.save_note(note)
        self.editor.save_button.setEnabled(False)
        QMessageBox.information(self, "Gespeichert", "Notiz wurde gespeichert.")

    def _on_delete_note(self, note: Note):
        reply = QMessageBox.question(
            self,
            "Notiz löschen",
            f'Soll "{note.title}" wirklich gelöscht werden?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._controller.delete_note(note)
            self.stack.setCurrentIndex(0)

    def _on_refresh(self):
        if self._controller:
            self._controller.refresh()



