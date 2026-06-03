"""Detección de duplicados (PRD RF-15, sección 13).

La lógica de coincidencia es pura y testable (`is_duplicate` / `find_duplicate`).
`detect_duplicate` es el contrato del PRD; en el MVP consulta Supabase, por lo
que recibe un `repo` inyectable (Protocol) para no acoplar la lógica a la BD.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Protocol


class ExistingInvoice(Protocol):
    """Proyección mínima de una factura ya registrada."""

    id: str
    nif_emisor: Optional[str]
    numero: Optional[str]
    total: Optional[float]
    fecha_expedicion: Optional[date]


def is_duplicate(
    nif_emisor: str,
    numero: str,
    total: float,
    fecha: date,
    other: ExistingInvoice,
    importe_tol: float = 0.01,
) -> bool:
    """¿`other` es el mismo documento? Emisor + número + importe + fecha."""
    if not other.nif_emisor or not other.numero:
        return False
    if other.nif_emisor.strip().upper() != nif_emisor.strip().upper():
        return False
    if other.numero.strip().upper() != numero.strip().upper():
        return False
    if other.total is None or abs(other.total - total) > importe_tol:
        return False
    if other.fecha_expedicion != fecha:
        return False
    return True


def find_duplicate(
    nif_emisor: str,
    numero: str,
    total: float,
    fecha: date,
    existing: list[ExistingInvoice],
    importe_tol: float = 0.01,
) -> Optional[str]:
    """Devuelve el id del primer duplicado en `existing`, o None."""
    for inv in existing:
        if is_duplicate(nif_emisor, numero, total, fecha, inv, importe_tol):
            return inv.id
    return None


class InvoiceRepo(Protocol):
    """Acceso a facturas candidatas de un tenant (implementado en Fase 2)."""

    def candidates_for_duplicate(
        self, tenant_id: str, nif_emisor: str, numero: str
    ) -> list[ExistingInvoice]: ...


def detect_duplicate(
    tenant_id: str,
    nif_emisor: str,
    numero: str,
    total: float,
    fecha: date,
    repo: InvoiceRepo,
    importe_tol: float = 0.01,
) -> Optional[str]:
    """Contrato del PRD: devuelve invoice_id si existe duplicado, si no None.

    `repo` desacopla la consulta a Supabase de la regla de coincidencia.
    """
    existing = repo.candidates_for_duplicate(tenant_id, nif_emisor, numero)
    return find_duplicate(nif_emisor, numero, total, fecha, existing, importe_tol)
