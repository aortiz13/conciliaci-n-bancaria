"""Servicio de extracción y validación de facturas (PRD secciones 10, 13).

Expone los modelos de dominio y las tools deterministas del MVP.
La extracción con LLM multimodal (`extract_invoice`) y el acceso real a
Supabase se implementan en la Fase 2; aquí vive la lógica pura y testable.
"""

from .duplicates import detect_duplicate, find_duplicate, is_duplicate
from .models import (
    ExtractedInvoice,
    InvoiceLine,
    InvoiceRoute,
    ReconCandidate,
    TaxSubtotal,
)
from .routing import campos_faltantes, route_invoice
from .validators import validate_iban, validate_nif, validate_vat_arithmetic

__all__ = [
    "ExtractedInvoice",
    "InvoiceLine",
    "InvoiceRoute",
    "ReconCandidate",
    "TaxSubtotal",
    "validate_nif",
    "validate_iban",
    "validate_vat_arithmetic",
    "detect_duplicate",
    "find_duplicate",
    "is_duplicate",
    "route_invoice",
    "campos_faltantes",
]
