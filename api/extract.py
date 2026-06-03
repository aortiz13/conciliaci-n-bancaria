"""Función serverless de extracción (Vercel Python).

Contrato HTTP (la invoca el workflow de Inngest tras persistir el documento):

    POST /api/extract
    { "tenant_id": "...", "document_id": "...",
      "storage_path": "<tenant>/<doc>.pdf", "mime": "application/pdf" }

Descarga el archivo del Storage privado, ejecuta el pipeline
(extracción + validación + dedupe + enrutado + persistencia) y devuelve el
resultado. El bucket por defecto es `invoices`.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# El paquete de extracción vive fuera de /api; se añade al path.
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "extraction")
)

from conciliacion_extraction.extraction import get_extractor  # noqa: E402
from conciliacion_extraction.pipeline import process_document  # noqa: E402
from conciliacion_extraction.repo import SupabaseRepo  # noqa: E402

BUCKET = os.getenv("INVOICES_BUCKET", "invoices")


def _run(body: dict) -> dict:
    tenant_id = body["tenant_id"]
    document_id = body.get("document_id")
    storage_path = body["storage_path"]
    mime = body.get("mime", "application/pdf")

    repo = SupabaseRepo()
    file_bytes = repo.download_object(BUCKET, storage_path)
    extractor = get_extractor()

    result = process_document(
        tenant_id=tenant_id,
        document_id=document_id,
        file_bytes=file_bytes,
        mime=mime,
        extractor=extractor,
        repo=repo,
    )
    return {
        "estado": result.estado,
        "invoice_id": result.invoice_id,
        "duplicate_of": result.duplicate_of,
        "validations": result.validations,
        "supplier_id": result.supplier_id,
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 (firma de la librería estándar)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
            payload = _run(body)
            status = 200
        except Exception as exc:  # noqa: BLE001 — se reporta al llamante (Inngest)
            payload = {"error": str(exc)}
            status = 500

        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
