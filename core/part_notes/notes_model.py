from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteType(str, Enum):
    CHECKLIST = "checklist"
    PLAIN_TEXT = "plain_text"
    IMAGE = "image"


class ChecklistItem(BaseModel):
    text: str
    checked: bool = False


class Note(BaseModel):
    id: str = Field(description="Google Drive file ID")
    title: str = Field(description="Note title (Drive file name without extension)")
    note_type: NoteType = Field(description="Type of note")
    content: str = Field(
        default="",
        description=(
            "For PLAIN_TEXT: the raw text content. "
            "For CHECKLIST: JSON array of ChecklistItem objects. "
            "For IMAGE: empty or description text."
        ),
    )
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    image_file_id: Optional[str] = Field(
        default=None,
        description="Drive file ID of the uploaded image (only for IMAGE type)",
    )
