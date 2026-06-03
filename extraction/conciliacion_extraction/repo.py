"""Repositorio Supabase para el pipeline (PostgREST + service_role).

Implementa `PipelineRepo` contra el esquema `conciliacion` usando httpx y la
service_role key (solo backend). El filtrado por `tenant_id` es explícito
(defense-in-depth, además de RLS).

Variables de entorno: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import httpx

from .models import ExtractedInvoice, InvoiceLine, InvoiceRoute, TaxSubtotal

SCHEMA = "conciliacion"


@dataclass
class _Row:
    """Proyección de factura existente (para deduplicación)."""

    id: str
    nif_emisor: Optional[str]
    numero: Optional[str]
    total: Optional[float]
    fecha_expedicion: Optional[date]


def _to_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class SupabaseRepo:
    """Acceso a datos del pipeline vía PostgREST."""

    def __init__(
        self, base_url: Optional[str] = None, service_key: Optional[str] = None
    ) -> None:
        self.base_url = (base_url or os.environ["SUPABASE_URL"]).rstrip("/")
        self.service_key = service_key or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self._client = httpx.Client(timeout=30.0)

    # -- helpers HTTP -------------------------------------------------------

    def _headers(self, write: bool = False, prefer: Optional[str] = None) -> dict:
        h = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            ("Content-Profile" if write else "Accept-Profile"): SCHEMA,
        }
        if prefer:
            h["Prefer"] = prefer
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url}/rest/v1/{path}"

    def _get(self, path: str, params: dict) -> list[dict]:
        r = self._client.get(
            self._url(path), params=params, headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    def _insert(self, table: str, payload: Any, returning: bool = False) -> Any:
        prefer = "return=representation" if returning else "return=minimal"
        r = self._client.post(
            self._url(table),
            json=payload,
            headers=self._headers(write=True, prefer=prefer),
        )
        r.raise_for_status()
        return r.json() if returning else None

    def _rpc(self, fn: str, payload: dict) -> Any:
        r = self._client.post(
            self._url(f"rpc/{fn}"),
            json=payload,
            headers=self._headers(write=True),
        )
        r.raise_for_status()
        return r.json() if r.content else None

    # -- PipelineRepo -------------------------------------------------------

    def candidates_for_duplicate(
        self, tenant_id: str, nif_emisor: str, numero: str
    ) -> list[_Row]:
        rows = self._get(
            "invoices",
            {
                "tenant_id": f"eq.{tenant_id}",
                "nif_emisor": f"eq.{nif_emisor}",
                "numero": f"eq.{numero}",
                "select": "id,nif_emisor,numero,total,fecha_expedicion",
            },
        )
        return [
            _Row(
                id=row["id"],
                nif_emisor=row.get("nif_emisor"),
                numero=row.get("numero"),
                total=row.get("total"),
                fecha_expedicion=_to_date(row.get("fecha_expedicion")),
            )
            for row in rows
        ]

    def find_or_create_supplier(
        self, tenant_id: str, nif: Optional[str]
    ) -> Optional[str]:
        if not nif:
            return None
        found = self._get(
            "suppliers",
            {
                "tenant_id": f"eq.{tenant_id}",
                "nif": f"eq.{nif}",
                "select": "id",
                "limit": "1",
            },
        )
        if found:
            return found[0]["id"]
        # Remitente nuevo desconocido → proveedor provisional en cuarentena.
        created = self._insert(
            "suppliers",
            {"tenant_id": tenant_id, "nif": nif, "estado": "provisional"},
            returning=True,
        )
        return created[0]["id"]

    def insert_invoice(
        self,
        tenant_id: str,
        supplier_id: Optional[str],
        document_id: Optional[str],
        inv: ExtractedInvoice,
        estado: InvoiceRoute,
        validations: list[str],
    ) -> str:
        created = self._insert(
            "invoices",
            {
                "tenant_id": tenant_id,
                "supplier_id": supplier_id,
                "document_id": document_id,
                "serie": inv.serie,
                "numero": inv.numero,
                "fecha_expedicion": inv.fecha_expedicion.isoformat(),
                "fecha_operacion": (
                    inv.fecha_operacion.isoformat() if inv.fecha_operacion else None
                ),
                "nif_emisor": inv.nif_emisor,
                "nif_receptor": inv.nif_receptor,
                "base_total": inv.base_total,
                "cuota_total": inv.cuota_total,
                "irpf": inv.irpf,
                "total": inv.total,
                "estado": estado,
                "confidence_global": inv.confidence_global,
            },
            returning=True,
        )
        return created[0]["id"]

    def insert_lines(
        self, tenant_id: str, invoice_id: str, lines: list[InvoiceLine]
    ) -> None:
        self._insert(
            "invoice_lines",
            [
                {
                    "tenant_id": tenant_id,
                    "invoice_id": invoice_id,
                    "descripcion": ln.descripcion,
                    "cantidad": ln.cantidad,
                    "precio_unit": ln.precio_unit,
                    "importe": ln.importe,
                    "tipo_iva": ln.tipo_iva,
                    "confidence": ln.confidence,
                }
                for ln in lines
            ],
        )

    def insert_tax_subtotals(
        self, tenant_id: str, invoice_id: str, subtotals: list[TaxSubtotal]
    ) -> None:
        self._insert(
            "invoice_tax_subtotals",
            [
                {
                    "tenant_id": tenant_id,
                    "invoice_id": invoice_id,
                    "tipo_iva": st.tipo_iva,
                    "base": st.base,
                    "cuota": st.cuota,
                }
                for st in subtotals
            ],
        )

    def enqueue_exception(
        self, tenant_id: str, tipo: str, ref_id: str, motivo: str
    ) -> None:
        self._insert(
            "exceptions_queue",
            {
                "tenant_id": tenant_id,
                "tipo": tipo,
                "ref_id": ref_id,
                "motivo": motivo,
            },
        )

    def record_audit(
        self, tenant_id: str, actor: str, accion: str, entidad: str, despues: dict
    ) -> None:
        self._insert(
            "audit_log",
            {
                "tenant_id": tenant_id,
                "actor": actor,
                "accion": accion,
                "entidad": entidad,
                "despues": despues,
            },
        )

    def increment_usage(self, tenant_id: str, periodo: str) -> None:
        # Incremento atómico vía función SQL (migración 0006).
        self._rpc(
            "increment_usage", {"p_tenant_id": tenant_id, "p_periodo": periodo}
        )

    # -- Storage ------------------------------------------------------------

    def download_object(self, bucket: str, path: str) -> bytes:
        """Descarga un archivo del Storage privado (service_role)."""
        r = self._client.get(
            f"{self.base_url}/storage/v1/object/{bucket}/{path}",
            headers={
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
            },
        )
        r.raise_for_status()
        return r.content
