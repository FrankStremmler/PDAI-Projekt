import os
import json
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from . import hb_prompts_constants as prompts
from .global_functions import get_file_type, encode_file_to_base64


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class ReceiptAnalyzer:
    """Beleganalyse mit OpenAI."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.client = OpenAI()

    def analyze_receipt(self, file_path):
        """Analysiert eine Quittung.

        - Prompt kommt aus hb_prompts_constants.MAIN_PROMPT
        - jpg/png: Datei wird zu Base64 konvertiert, NICHT in den Prompt geschrieben.
          Stattdessen wird die Base64 als Text-Datei bei OpenAI hochgeladen und über file_input referenziert.
        - andere Dateien: Upload wie zuvor und über file_input referenziert.

        Speichert Ergebnis als c:\\gespeichert\\response.json
        """
        if not os.path.exists(file_path):
            print("Datei nicht gefunden.")
            return None

        target_dir = r"c:\\gespeichert"
        os.makedirs(target_dir, exist_ok=True)
        out_path = os.path.join(target_dir, "response.json")

        try:
            # Token-sparend: Base64 wird als Datei hochgeladen, nicht in den Prompt geschrieben.
            base64_str = encode_file_to_base64(file_path)
            base64_upload_content = (
                "IMAGE_BASE64_BEGIN\n"
                f"{base64_str}\n"
                "IMAGE_BASE64_END"
            )

            from io import BytesIO

            with BytesIO(base64_upload_content.encode("utf-8")) as bio:
                uploaded_file = self.client.files.create(
                    file=bio,
                    purpose="user_data",
                )

            file_id = uploaded_file.id
            print(f"Erfolgreich hochgeladen (Base64). Datei-ID: {file_id}")

        except Exception as e:
            print(f"Fehler beim Hochladen der Datei: {str(e)}")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts.MAIN_PROMPT},
                    {"type": "file_input", "file_id": file_id},
                ],
            }
        ]

        print("2. Analyse starten...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        content = response.choices[0].message.content
        if content is None:
            return None

        # Robust: JSON direkt parsen oder JSON-Teil extrahieren
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                parsed = json.loads(content[start : end + 1])
            else:
                parsed = {"raw_response": content}

        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(parsed, fp, ensure_ascii=False, indent=2)

        return parsed

    # except Exception as e:
    #     print(f"Fehler bei der OpenAI-Verarbeitung: {str(e)}")
    #     return None

