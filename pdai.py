"""Projekt-Einstieg.

Dieses Modul ist die Entry-Point-Datei und startet die PySide6-GUI.
"""

from __future__ import annotations

import sys


def main() -> int:
    # Start der GUI über die dafür vorgesehene Einstiegspunkte-Datei.
    from pdai_gui.main import run_app

    return int(run_app())


if __name__ == "__main__":
    sys.exit(main())

