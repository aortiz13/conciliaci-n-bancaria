"""Enrutado de la factura tras la extracción (PRD RF-11, flujos A/B, sección 13).

Decide el estado inicial según completitud, validaciones y confidence:
  - registrada:          campos obligatorios OK + sin errores + confidence alto.
  - registrada_revision: legible pero con faltantes/errores o confidence medio
                         (se registra igual, no bloquea — modelo B).
  - escalada:            documento sin datos utilizables / confidence muy bajo.
"""

from __future__ import annotations

from .models import ExtractedInvoice, InvoiceRoute

# Umbrales de confidence global.
CONFIDENCE_ALTA = 0.85
CONFIDENCE_MINIMA = 0.40

# Campos de cabecera obligatorios para considerar la factura "registrable".
_CAMPOS_OBLIGATORIOS = (
    "numero",
    "fecha_expedicion",
    "nif_emisor",
    "base_total",
    "cuota_total",
    "total",
)


def campos_faltantes(inv: ExtractedInvoice) -> list[str]:
    """Lista de campos obligatorios ausentes o vacíos."""
    faltan: list[str] = []
    for campo in _CAMPOS_OBLIGATORIOS:
        valor = getattr(inv, campo, None)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            faltan.append(campo)
    return faltan


def route_invoice(
    inv: ExtractedInvoice, validations: list[str]
) -> InvoiceRoute:
    """Enrutado por completitud + validaciones + confidence.

    `validations` es la lista de errores acumulados (NIF/IBAN/IVA, etc.);
    vacía significa que todas las validaciones pasaron.
    """
    faltan = campos_faltantes(inv)

    # Sin datos mínimos identificables o confianza ínfima → a humano.
    sin_identificadores = "numero" in faltan and "nif_emisor" in faltan
    if inv.confidence_global < CONFIDENCE_MINIMA or sin_identificadores:
        return "escalada"

    # Completa, válida y con alta confianza → STP.
    if not faltan and not validations and inv.confidence_global >= CONFIDENCE_ALTA:
        return "registrada"

    # Legible pero con dudas → se registra y entra a revisión (no bloquea).
    return "registrada_revision"
