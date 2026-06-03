"""Modelos de dominio de extracción (PRD sección 13).

Los tipos reflejan las firmas del PRD. Se usan `float` para importes por
fidelidad al documento; las comparaciones aritméticas se hacen siempre con
tolerancia (ver `validators.validate_vat_arithmetic`).
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Tipos de IVA admitidos en el MVP (general, reducido, superreducido, exento).
TipoIVA = Literal[21, 10, 4, 0]


class TaxSubtotal(BaseModel):
    """Subtotal de impuesto por tipo de IVA."""

    tipo_iva: TipoIVA
    base: float
    cuota: float


class InvoiceLine(BaseModel):
    """Línea de detalle de la factura."""

    descripcion: str
    cantidad: float
    precio_unit: float
    importe: float
    tipo_iva: TipoIVA
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedInvoice(BaseModel):
    """Factura extraída por el LLM multimodal con confidence por campo."""

    serie: Optional[str] = None
    numero: str
    fecha_expedicion: date
    fecha_operacion: Optional[date] = None
    nif_emisor: str
    nif_receptor: Optional[str] = None
    base_total: float
    cuota_total: float
    irpf: float = 0.0  # línea negativa (15% / 7%)
    total: float
    lines: list[InvoiceLine] = Field(default_factory=list)
    tax_subtotals: list[TaxSubtotal] = Field(default_factory=list)
    iban: Optional[str] = None
    confidence_global: float = Field(ge=0.0, le=1.0)


class ReconCandidate(BaseModel):
    """Candidato de conciliación factura ↔ movimiento bancario."""

    movement_id: str
    score: float
    tipo: Literal["1:1", "1:N", "N:1", "parcial"]
    razon: str


# Estado de enrutado de una factura recién registrada.
InvoiceRoute = Literal["registrada", "registrada_revision", "escalada"]
