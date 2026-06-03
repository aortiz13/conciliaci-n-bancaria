"""Extracción de facturas con LLM multimodal (PRD RF-10, sección 13).

Abstracción `InvoiceExtractor` con una implementación para Gemini 2.5 vía
Vertex AI (región UE). El SDK de Google se importa de forma perezosa para que
el paquete y los tests funcionen sin credenciales ni dependencias pesadas.

Estrategia de coste (PRD §11): primer pase con Flash; si el confidence global
es bajo, se reintenta con Pro.
"""

from __future__ import annotations

import json
import os
from typing import Protocol

from .models import ExtractedInvoice

MODEL_FLASH = os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
MODEL_PRO = os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")

# Umbral por debajo del cual se reintenta con el modelo Pro.
ESCALATE_TO_PRO_BELOW = float(os.getenv("EXTRACTION_PRO_THRESHOLD", "0.85"))

_PROMPT = """\
Eres un extractor de facturas españolas. Devuelve EXCLUSIVAMENTE un JSON válido
con esta forma (sin texto adicional, sin markdown):

{
  "serie": string|null,
  "numero": string,
  "fecha_expedicion": "YYYY-MM-DD",
  "fecha_operacion": "YYYY-MM-DD"|null,
  "nif_emisor": string,
  "nif_receptor": string|null,
  "base_total": number,
  "cuota_total": number,
  "irpf": number,
  "total": number,
  "lines": [{"descripcion": string, "cantidad": number, "precio_unit": number,
             "importe": number, "tipo_iva": 21|10|4|0, "confidence": number}],
  "tax_subtotals": [{"tipo_iva": 21|10|4|0, "base": number, "cuota": number}],
  "iban": string|null,
  "confidence_global": number
}

Reglas:
- Importes con punto decimal. IRPF como número positivo (es una retención).
- `confidence_global` y `confidence` por línea entre 0 y 1, reflejando tu
  certeza real sobre la lectura.
- Si un campo no aparece, usa null (o 0 en los importes que no apliquen).
"""


class InvoiceExtractor(Protocol):
    """Contrato de un extractor de facturas."""

    def extract(self, file_bytes: bytes, mime: str) -> ExtractedInvoice: ...


def parse_invoice_json(payload: str) -> ExtractedInvoice:
    """Parsea la respuesta JSON del LLM a `ExtractedInvoice` (tolerante a fences)."""
    text = payload.strip()
    if text.startswith("```"):
        text = text.strip("`")
        # quitar un posible prefijo de lenguaje ("json\n...")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    data = json.loads(text)
    return ExtractedInvoice.model_validate(data)


class GeminiExtractor:
    """Extractor basado en Gemini multimodal (Vertex AI, región UE).

    Importa el SDK de Google de forma perezosa. Requiere las variables
    `VERTEX_PROJECT_ID` y `VERTEX_LOCATION` (y credenciales ADC).
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
    ) -> None:
        self.project_id = project_id or os.environ["VERTEX_PROJECT_ID"]
        self.location = location or os.getenv("VERTEX_LOCATION", "europe-west1")

    def _client(self):
        # Import perezoso: el paquete no depende del SDK en tiempo de carga.
        from google import genai  # type: ignore

        return genai.Client(
            vertexai=True, project=self.project_id, location=self.location
        )

    def _call(self, model: str, file_bytes: bytes, mime: str) -> ExtractedInvoice:
        from google.genai import types  # type: ignore

        client = self._client()
        response = client.models.generate_content(
            model=model,
            contents=[
                _PROMPT,
                types.Part.from_bytes(data=file_bytes, mime_type=mime),
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        return parse_invoice_json(response.text)

    def extract(self, file_bytes: bytes, mime: str) -> ExtractedInvoice:
        inv = self._call(MODEL_FLASH, file_bytes, mime)
        if inv.confidence_global < ESCALATE_TO_PRO_BELOW:
            # Segundo pase con el modelo más capaz para reducir excepciones.
            inv = self._call(MODEL_PRO, file_bytes, mime)
        return inv


def get_extractor() -> InvoiceExtractor:
    """Factoría del extractor por defecto (Gemini)."""
    return GeminiExtractor()
