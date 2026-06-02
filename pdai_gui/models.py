from dataclasses import dataclass
from typing import Callable, List


@dataclass
class AppEntry:
    id: str
    name: str
    factory: Callable[[], object]


class AppModel:
    """Hält die Registrierung der Sub-Apps."""
    def __init__(self):
        self.apps: List[AppEntry] = []

    def register(self, id: str, name: str, factory: Callable[[], object]):
        self.apps.append(AppEntry(id=id, name=name, factory=factory))

    def list(self) -> List[AppEntry]:
        return list(self.apps)
