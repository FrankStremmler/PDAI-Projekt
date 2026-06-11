# hb_file_input_controller.py
import os
from typing import Optional
from openai import OpenAI

# Import der MVC-Konstanten und Text-Prompts
from hb_prompts_constants import (
    INPUT_DIR,
    ALLOWED_EXTENSIONS,
    OPENAI_MODEL,
    PROMPT_BANK_STATEMENT,
    PROMPT_RECEIPT
)

# Import der zentralen Pydantic-Validierungsmodelle aus der Basis-Datei
from hb_base import BankStatementSchema, ReceiptSchema

# Import des vorhandenen Hilfsmoduls für Dateioperationen und Encodings
import providers.openai_functions as openai_utils


class FileInputController:
    """
    MVC-Controller für die Erfassung von Belegen und Bankauszügen.
    Überwacht Eingabeordner und steuert die strukturierte Extraktion via OpenAI.
    """
    def __init__(self):
        # Initialisierung des OpenAI-Clients.
        # Erwartet den API-Key automatisch in os.environ["OPENAI_API_KEY"]
        self.client = OpenAI()

        # Sicherstellen, dass das Eingangsverzeichnis existiert
        if not os.path.exists(INPUT_DIR):
            os.makedirs(INPUT_DIR)

    def scan_input_folder(self) -> list[str]:
        """
        Durchsucht das Eingangsverzeichnis nach neuen Dokumenten,
        deren Dateiendung in den erlaubten Typen definiert ist.

        Returns:
            list[str]: Eine Liste mit den relativen Pfaden zu den gefundenen Dateien.
        """
        found_files = []
        for file in os.listdir(INPUT_DIR):
            ext = os.path.splitext(file).lower()
            if ext in ALLOWED_EXTENSIONS:
                found_files.append(os.path.join(INPUT_DIR, file))
        return found_files

    def analyze_document(self, file_path: str, doc_type: str) -> Optional[dict]:
        """
        Analysiert ein Dokument (PDF oder Bild) mithilfe der OpenAI-API.
        Zwingt gpt-4.1-mini zur Einhaltung des Pydantic-Schemas.

        Args:
            file_path (str): Der Pfad zur zu analysierenden Datei.
            doc_type (str): Der Typ des Dokuments ('bank' oder 'receipt').

        Returns:
            Optional[dict]: Das validierte Ergebnis als Python-Dictionary oder None im Fehlerfall.
        """
        if not os.path.exists(file_path):
            print(f"[Input-Controller] Fehler: Datei existiert nicht: {file_path}")
            return None

        print(f"[Input-Controller] Starte Analyse für '{os.path.basename(file_path)}' ({doc_type}) via {OPENAI_MODEL}...")

        # Nutzen der vorhandenen Funktion aus providers/openai_functions.py
        # Verarbeitet PDFs direkt oder encodiert Bilder bei Bedarf zu Base64
        file_data = openai_utils.upload_file_to_ai(file_path)

        # Zuweisung von Text-Prompts und Ziel-Schema basierend auf dem Dokumententyp
        if doc_type == "bank":
            system_prompt = PROMPT_BANK_STATEMENT
            target_schema = BankStatementSchema
        elif doc_type == "receipt":
            system_prompt = PROMPT_RECEIPT
            target_schema = ReceiptSchema
        else:
            raise ValueError("[Input-Controller] Ungültiger doc_type. Erlaubt sind nur 'bank' oder 'receipt'.")

        try:
            # API-Aufruf über das strukturierte Beta-Parsing-Modul von OpenAI
            response = self.client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extrahiere die strukturierten Daten aus diesem Dokument für das Haushaltsbuch."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    # Dynamische Übergabe des Mime-Types und des Datei-Inhalts aus Ihrer providers-Funktion
                                    "url": f"data:{file_data['file_type']};base64,{file_data['file_content']}"
                                }
                            }
                        ]
                    }
                ],
                response_format=target_schema,  # Erzwingt die exakte Strukturierung auf Token-Ebene
                temperature=0.1                 # Niedriger Wert für höchste Datentreue und Faktenstabilität
            )

            # Das fertig validierte Pydantic-Objekt aus der Antwort ziehen
            parsed_result = response.choices.message.parsed

            if parsed_result:
                # Konvertiert das Pydantic-Modell in ein reines Python-Dictionary für den CRUD-Controller
                return parsed_result.model_dump()

            print("[Input-Controller] Fehler: KI-Antwort konnte nicht in das Schema geparset werden.")
            return None

        except Exception as e:
            print(f"[Input-Controller] Kritischer Fehler bei der OpenAI-API-Verarbeitung: {e}")
            return None


# Modultest (wird nur ausgeführt, wenn die Datei direkt gestartet wird)
if __name__ == "__main__":
    # Testen Sie hier die Erkennung, falls Testdateien im Ordner liegen
    controller = FileInputController()
    dateien = controller.scan_input_folder()
    print(f"[Test] Gefundene Dateien im Eingangsordner: {dateien}")

