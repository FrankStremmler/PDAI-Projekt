from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DriveItem:
    id: str
    name: str
    mime_type: str
    is_folder: bool


@dataclass
class DriveFolderState:
    current_folder_id: str = "root"
    current_path: Optional[List[str]] = None
    items: Optional[List[DriveItem]] = None

    def __post_init__(self):
        if self.current_path is None:
            self.current_path = []
        if self.items is None:
            self.items = []

