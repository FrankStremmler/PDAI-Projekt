import os
import base64
import mimetypes
from dotenv import load_dotenv
from typing import Optional
from PySide6.QtCore import QObject, Signal

from ..pdf_utils import pdf_to_jpeg_bytes
from .hb_base import NormalizedReceipt, NormalizedBankStatement
from .hb_config_model import ConfigManager
from standards_and_constants.hb_prompts_constants import (
    PROVIDER_OPENAI, PROVIDER_GEMINI, MODEL_OPENAI, MODEL_GEMINI,
    PROMPT_RECEIPT, PROMPT_BANK_STATEMENT, MIME_PDF,
)

load_dotenv()


class AIPlatformWrapper(QObject):
    status_changed = Signal(str)
    analysis_completed = Signal(object)
    analysis_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.provider = self.config_manager.config.ai_provider.lower()

    def analyze_receipt(self, file_path: str, mime_type: str) -> Optional[NormalizedReceipt]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

        if self.provider == PROVIDER_OPENAI:
            return self._analyze_with_openai(file_path, mime_type, PROMPT_RECEIPT, NormalizedReceipt)
        return self._analyze_with_gemini(file_path, mime_type, PROMPT_RECEIPT, NormalizedReceipt)

    def analyze_bank_statement(self, file_path: str, mime_type: str) -> Optional[NormalizedBankStatement]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

        if self.provider == PROVIDER_OPENAI:
            return self._analyze_with_openai(file_path, mime_type, PROMPT_BANK_STATEMENT, NormalizedBankStatement)
        return self._analyze_with_gemini(file_path, mime_type, PROMPT_BANK_STATEMENT, NormalizedBankStatement)

    def _build_user_content(self, file_path: str, mime_type: str, prompt: str):
        is_pdf = mime_type == MIME_PDF
        if is_pdf:
            self.status_changed.emit("Konvertiere PDF in Bilder...")
            page_images = pdf_to_jpeg_bytes(file_path)
            content: list[dict] = [{"type": "text", "text": prompt}]
            for img_bytes in page_images:
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
            print(f"[AI] PDF konvertiert: {len(page_images)} Seite(n) als JPEG")
            return content, None, None
        else:
            mime, _ = mimetypes.guess_type(file_path)
            mime = mime or mime_type
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
            ], None, None

    def _parse_openai_response(self, response, target_model):
        parsed = response.choices[0].message.parsed
        if parsed:
            return parsed
        raw = response.choices[0].message.content
        if raw:
            return target_model.model_validate_json(raw)
        raise ValueError("Keine Antwort von der KI erhalten.")

    def _analyze_with_openai(self, file_path, mime_type, prompt, target_model):
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY in .env nicht gesetzt")

        client = OpenAI(api_key=api_key)
        user_content, file_id, upload_client = self._build_user_content(file_path, mime_type, prompt)

        try:
            self.status_changed.emit(f"KI-Analyse mit {MODEL_OPENAI}...")
            response = client.beta.chat.completions.parse(
                model=MODEL_OPENAI,
                messages=[{"role": "user", "content": user_content}],
                response_format=target_model,
                temperature=0.1,
            )

            result = self._parse_openai_response(response, target_model)
            print(f"[AI-Output]: {result.model_dump_json()}")
            self.status_changed.emit("Analyse erfolgreich abgeschlossen.")
            self.analysis_completed.emit(result)
            return result

        except Exception as e:
            error_msg = f"OpenAI-Fehler: {e}"
            print(f"[AI] {error_msg}")
            self.analysis_failed.emit(error_msg)
            raise e

        finally:
            if file_id and upload_client:
                try:
                    upload_client.files.delete(file_id)
                    print(f"[AI] Server-Cleanup: {file_id}")
                except Exception as e:
                    print(f"[AI] Cleanup-Warnung: {e}")

    def _analyze_with_gemini(self, file_path, mime_type, prompt, target_model):
        from providers.google_parts.gemini import get_client, generate_structured

        client = get_client()
        uploaded_file = None

        try:
            self.status_changed.emit(f"KI-Analyse mit {MODEL_GEMINI}...")
            result_text, uploaded_file = generate_structured(
                client, MODEL_GEMINI, prompt, file_path, mime_type, target_model
            )

            result = target_model.model_validate_json(result_text)
            print(f"[AI-Output]: {result.model_dump_json()}")
            self.status_changed.emit("Analyse erfolgreich abgeschlossen.")
            self.analysis_completed.emit(result)
            return result

        except Exception as e:
            error_msg = f"Gemini-Fehler: {e}"
            print(f"[AI] {error_msg}")
            self.analysis_failed.emit(error_msg)
            raise e

        finally:
            if uploaded_file is not None:
                try:
                    client.files.delete(name=uploaded_file.name)
                    print(f"[Gemini] Cleanup: {uploaded_file.name}")
                except Exception:
                    pass
