import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class ReceiptAnalyzer:
    """Placeholder-Service für Beleganalyse mit OpenAI."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL

    def analyze_receipt(self, source_path: str) -> dict:
        """Analysiert einen Belegbild- oder PDF-Pfad. Funktionalität noch ausstehend."""
        return {
            "source": source_path,
            "status": "pending",
            "message": "Analyse-Funktion ist aktuell nicht implementiert.",
        }
