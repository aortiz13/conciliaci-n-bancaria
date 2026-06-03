"""Tests de orquestación del pipeline (con extractor y repo falsos)."""

from datetime import date
from typing import Optional

from conciliacion_extraction.duplicates import ExistingInvoice
from conciliacion_extraction.models import (
    ExtractedInvoice,
    InvoiceLine,
    InvoiceRoute,
    TaxSubtotal,
)
from conciliacion_extraction.pipeline import process_document


def _invoice(**kwargs) -> ExtractedInvoice:
    base = dict(
        numero="2026-001",
        fecha_expedicion=date(2026, 1, 15),
        nif_emisor="A58818501",
        base_total=100.0,
        cuota_total=21.0,
        irpf=0.0,
        total=121.0,
        lines=[
            InvoiceLine(
                descripcion="Servicio",
                cantidad=1,
                precio_unit=100.0,
                importe=100.0,
                tipo_iva=21,
                confidence=0.95,
            )
        ],
        tax_subtotals=[TaxSubtotal(tipo_iva=21, base=100.0, cuota=21.0)],
        confidence_global=0.95,
    )
    base.update(kwargs)
    return ExtractedInvoice(**base)


class FakeExtractor:
    def __init__(self, inv: ExtractedInvoice) -> None:
        self.inv = inv

    def extract(self, file_bytes: bytes, mime: str) -> ExtractedInvoice:
        return self.inv


class FakeRepo:
    def __init__(self, existing: Optional[list[ExistingInvoice]] = None) -> None:
        self.existing = existing or []
        self.invoices: list[dict] = []
        self.lines: list = []
        self.subtotals: list = []
        self.exceptions: list[dict] = []
        self.audits: list[dict] = []
        self.usage: list[tuple[str, str]] = []
        self.suppliers: dict[str, str] = {}

    def candidates_for_duplicate(self, tenant_id, nif_emisor, numero):
        return self.existing

    def find_or_create_supplier(self, tenant_id, nif):
        if nif is None:
            return None
        return self.suppliers.setdefault(nif, f"sup-{nif}")

    def insert_invoice(self, tenant_id, supplier_id, document_id, inv, estado, validations):
        inv_id = f"inv-{len(self.invoices) + 1}"
        self.invoices.append(
            {"id": inv_id, "estado": estado, "supplier_id": supplier_id}
        )
        return inv_id

    def insert_lines(self, tenant_id, invoice_id, lines):
        self.lines.extend(lines)

    def insert_tax_subtotals(self, tenant_id, invoice_id, subtotals):
        self.subtotals.extend(subtotals)

    def enqueue_exception(self, tenant_id, tipo, ref_id, motivo):
        self.exceptions.append({"tipo": tipo, "ref_id": ref_id, "motivo": motivo})

    def record_audit(self, tenant_id, actor, accion, entidad, despues):
        self.audits.append({"accion": accion, "entidad": entidad})

    def increment_usage(self, tenant_id, periodo):
        self.usage.append((tenant_id, periodo))


def test_factura_valida_registrada():
    repo = FakeRepo()
    result = process_document(
        "t1", "doc1", b"bytes", "application/pdf",
        FakeExtractor(_invoice()), repo,
    )
    assert result.estado == "registrada"
    assert result.invoice_id == "inv-1"
    assert len(repo.invoices) == 1
    assert len(repo.lines) == 1
    assert len(repo.subtotals) == 1
    assert repo.exceptions == []          # STP, sin excepción
    # El uso se contabiliza en el periodo de procesamiento (mes actual).
    assert len(repo.usage) == 1
    tenant, periodo = repo.usage[0]
    assert tenant == "t1"
    assert len(periodo) == 7 and periodo[4] == "-"
    assert repo.audits and repo.audits[0]["accion"] == "invoice.registrada"
    assert result.supplier_id == "sup-A58818501"


def test_factura_incoherente_va_a_revision():
    repo = FakeRepo()
    inv = _invoice(total=999.0)  # rompe la aritmética de IVA
    result = process_document(
        "t1", "doc1", b"bytes", "application/pdf", FakeExtractor(inv), repo
    )
    assert result.estado == "registrada_revision"
    assert len(repo.exceptions) == 1
    assert repo.exceptions[0]["tipo"] == "dato_faltante"
    assert result.validations


def test_duplicado_no_inserta():
    class Existing:
        id = "inv-existente"
        nif_emisor = "A58818501"
        numero = "2026-001"
        total = 121.0
        fecha_expedicion = date(2026, 1, 15)

    repo = FakeRepo(existing=[Existing()])
    result = process_document(
        "t1", "doc1", b"bytes", "application/pdf",
        FakeExtractor(_invoice()), repo,
    )
    assert result.estado == "duplicada"
    assert result.duplicate_of == "inv-existente"
    assert repo.invoices == []            # no se inserta
    assert repo.usage == []
