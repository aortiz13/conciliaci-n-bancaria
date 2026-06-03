"""Orquestación del procesamiento de un documento (PRD flujo A, sección 7).

extract → validar (NIF/IBAN/IVA) → deduplicar → resolver proveedor →
enrutar → persistir → (excepción si revisión) → auditar/contar uso.

La persistencia y el acceso a datos se abstraen en `PipelineRepo` para poder
testear la lógica con un repo falso (sin Supabase ni LLM).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Protocol

from .duplicates import ExistingInvoice, find_duplicate
from .extraction import InvoiceExtractor
from .models import ExtractedInvoice, InvoiceLine, InvoiceRoute, TaxSubtotal
from .routing import route_invoice
from .validators import validate_iban, validate_nif, validate_vat_arithmetic


class PipelineRepo(Protocol):
    """Acceso a datos necesario para procesar un documento."""

    def candidates_for_duplicate(
        self, tenant_id: str, nif_emisor: str, numero: str
    ) -> list[ExistingInvoice]: ...

    def find_or_create_supplier(
        self, tenant_id: str, nif: Optional[str]
    ) -> Optional[str]: ...

    def insert_invoice(
        self,
        tenant_id: str,
        supplier_id: Optional[str],
        document_id: Optional[str],
        inv: ExtractedInvoice,
        estado: InvoiceRoute,
        validations: list[str],
    ) -> str: ...

    def insert_lines(
        self, tenant_id: str, invoice_id: str, lines: list[InvoiceLine]
    ) -> None: ...

    def insert_tax_subtotals(
        self, tenant_id: str, invoice_id: str, subtotals: list[TaxSubtotal]
    ) -> None: ...

    def enqueue_exception(
        self, tenant_id: str, tipo: str, ref_id: str, motivo: str
    ) -> None: ...

    def record_audit(
        self, tenant_id: str, actor: str, accion: str, entidad: str, despues: dict
    ) -> None: ...

    def increment_usage(self, tenant_id: str, periodo: str) -> None: ...


@dataclass
class ProcessResult:
    estado: str
    invoice_id: Optional[str] = None
    duplicate_of: Optional[str] = None
    validations: list[str] = field(default_factory=list)
    supplier_id: Optional[str] = None


def _collect_validations(inv: ExtractedInvoice) -> list[str]:
    """Ejecuta NIF/IBAN/IVA y devuelve la lista de errores legibles."""
    errores: list[str] = []

    ok, motivo = validate_nif(inv.nif_emisor)
    if not ok:
        errores.append(f"NIF emisor inválido: {motivo}")

    if inv.nif_receptor:
        ok, motivo = validate_nif(inv.nif_receptor)
        if not ok:
            errores.append(f"NIF receptor inválido: {motivo}")

    if inv.iban:
        ok, motivo = validate_iban(inv.iban)
        if not ok:
            errores.append(f"IBAN inválido: {motivo}")

    ok, vat_errs = validate_vat_arithmetic(inv)
    if not ok:
        errores.extend(vat_errs)

    return errores


def process_document(
    tenant_id: str,
    document_id: Optional[str],
    file_bytes: bytes,
    mime: str,
    extractor: InvoiceExtractor,
    repo: PipelineRepo,
) -> ProcessResult:
    """Procesa un documento de principio a fin. Idempotente ante duplicados."""
    inv = extractor.extract(file_bytes, mime)

    # Deduplicación (RF-15): si ya existe, no se inserta de nuevo.
    existing = repo.candidates_for_duplicate(tenant_id, inv.nif_emisor, inv.numero)
    dup_id = find_duplicate(
        inv.nif_emisor, inv.numero, inv.total, inv.fecha_expedicion, existing
    )
    if dup_id:
        return ProcessResult(estado="duplicada", duplicate_of=dup_id)

    validations = _collect_validations(inv)
    estado: InvoiceRoute = route_invoice(inv, validations)

    supplier_id = repo.find_or_create_supplier(tenant_id, inv.nif_emisor)

    invoice_id = repo.insert_invoice(
        tenant_id, supplier_id, document_id, inv, estado, validations
    )
    if inv.lines:
        repo.insert_lines(tenant_id, invoice_id, inv.lines)
    if inv.tax_subtotals:
        repo.insert_tax_subtotals(tenant_id, invoice_id, inv.tax_subtotals)

    if estado == "registrada_revision":
        motivo = "; ".join(validations) if validations else "Campos a revisar"
        repo.enqueue_exception(tenant_id, "dato_faltante", invoice_id, motivo)

    repo.increment_usage(tenant_id, _current_period())
    repo.record_audit(
        tenant_id,
        actor="system",
        accion="invoice.registrada",
        entidad=invoice_id,
        despues={"estado": estado, "validations": validations},
    )

    return ProcessResult(
        estado=estado,
        invoice_id=invoice_id,
        validations=validations,
        supplier_id=supplier_id,
    )


def _current_period(today: Optional[date] = None) -> str:
    d = today or datetime.now(timezone.utc).date()
    return f"{d.year:04d}-{d.month:02d}"
