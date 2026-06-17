import os
from .hb_file_input_controller import AIPlatformWrapper
from .hb_crud_controller import CrudController
from .hb_database import ensure_database
from standards_and_constants.hb_prompts_constants import SUPPORTED_EXTENSIONS


class ReceiptAnalyzer:
    def __init__(self):
        self.wrapper = AIPlatformWrapper()

    def analyze_receipt(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            print("Datei nicht gefunden.")
            return False

        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        mime_type = SUPPORTED_EXTENSIONS.get(ext, "application/octet-stream")

        try:
            result = self.wrapper.analyze_receipt(file_path, mime_type)
            if not result:
                return False

            db = ensure_database()
            crud = CrudController(db)
            if crud.find_duplicate_receipt(result):
                print(f"[ReceiptAnalyzer] Beleg vorhanden: {result.date_time} | {result.merchant} | {result.total_sum:.2f} €")
                return False
            return crud.save_receipt(result)
        except Exception as e:
            print(f"[ReceiptAnalyzer] Fehler: {e}")
            return False
