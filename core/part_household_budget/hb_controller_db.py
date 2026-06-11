# database_controller.py
import os
import shutil
from sqlalchemy import create_engine
from hb_model_db import Base  # Importiert das reine Datenmodell
from hb_prompts_constants import DB_NAME

class DatabaseController:
    def __init__(self):
        # Solange Cloud-Wrapper fehlt, ist die HDD-Datei unsere "Master-Datei"
        self.master_db_path = os.path.abspath(DB_NAME)

        # SQLAlchemy arbeitet IMMER im Temp-Ordner
        self.working_db_path = TEMP_DB_PATH
        self.db_uri = f"sqlite:///{self.working_db_path}"
        self._engine = None

    def prepare_working_directory(self) -> None:
        """
        Stufe 1 (Lokale HDD-Phase): Simuliert den Cloud-Download.
        Kopiert die Master-DB von der HDD in den Temp-Ordner.
        Existiert keine Master-DB, wird eine leere Datei im Temp-Ordner vorbereitet.
        """
        if os.path.exists(self.master_db_path):
            print(f"[Controller] Lade Master-DB in Temp-Ordner: {self.working_db_path}")
            shutil.copy2(self.master_db_path, self.working_db_path)
        else:
            print("[Controller] Keine Master-DB gefunden. Erstelle frische Arbeitsdatei im Temp-Ordner.")
            # Falls die Datei nicht existiert, sorgt create_db() gleich für die Erstellung

    def create_db(self) -> None:
        """
        Prüft die Arbeitsdatei im Temp-Ordner und generiert bei Bedarf das Schema.
        """
        # Vorbereitung des Temp-Ordners anstoßen
        self.prepare_working_directory()

        # Engine auf die Temp-Datei ansetzen
        self._engine = create_engine(self.db_uri, echo=False)

        # Prüfen, ob die Tabellen im Temp-File generiert werden müssen
        # (Entweder weil die Master-DB neu ist oder noch gar keine Datei existierte)
        # SQLite erstellt die Datei automatisch im Temp-Ordner bei 'create_all'
        Base.metadata.create_all(self._engine)
        print("[Controller] Datenbank im Temp-Ordner ist einsatzbereit.")

    def save_and_sync_back(self) -> None:
        """
        Stufe 3 (Upload-Phase): Kopiert die bearbeitete DB aus dem Temp-Ordner
        zurück auf das Master-Medium (Aktuell HDD, später Google Drive Upload).
        """
        if self._engine:
            # Engine sauber schließen, damit keine File-Locks auf der SQLite-Datei liegen
            self._engine.dispose()

        if os.path.exists(self.working_db_path):
            print(f"[Controller] Synchronisiere Änderungen zurück auf Master-Medium: {self.master_db_path}")
            shutil.copy2(self.working_db_path, self.master_db_path)
            # Optional: Temp-Datei nach dem Upload löschen
            # os.remove(self.working_db_path)
        else:
            print("[Controller] Fehler: Keine Arbeitsdatei zum Synchronisieren gefunden.")

    def get_engine(self):
        """Liefert die aktive Engine für die SQLAlchemy-Sessions im Temp-Ordner."""
        if not self._engine:
            self._engine = create_engine(self.db_uri)
        return self._engine