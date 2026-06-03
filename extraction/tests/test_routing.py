"""Tests del enrutado de facturas (route_invoice / campos_faltantes)."""

from datetime import date

from conciliacion_extraction.models import ExtractedInvoice
from conciliacion_extraction.routing import campos_faltantes, route_invoice


def _inv(**kwargs) -> ExtractedInvoice:
    base = dict(
        numero="A-1",
        fecha_expedicion=date(2026, 1, 15),
        nif_emisor="A58818501",
        base_total=100.0,
        cuota_total=21.0,
        irpf=0.0,
        total=121.0,
        confidence_global=0.95,
    )
    base.update(kwargs)
    return ExtractedInvoice(**base)


def test_registrada_stp():
    assert route_invoice(_inv(), []) == "registrada"


def test_revision_por_validaciones():
    assert route_invoice(_inv(), ["NIF inválido"]) == "registrada_revision"


def test_revision_por_confidence_media():
    assert route_invoice(_inv(confidence_global=0.6), []) == "registrada_revision"


def test_revision_por_campo_faltante():
    # Número vacío pero con NIF: legible → revisión, no bloquea.
    assert route_invoice(_inv(numero=""), []) == "registrada_revision"


def test_escalada_por_confidence_minima():
    assert route_invoice(_inv(confidence_global=0.2), []) == "escalada"


def test_escalada_sin_identificadores():
    inv = _inv(numero="", nif_emisor="")
    assert route_invoice(inv, []) == "escalada"


def test_campos_faltantes_detecta_vacios():
    inv = _inv(numero="   ", nif_emisor="")
    faltan = campos_faltantes(inv)
    assert "numero" in faltan
    assert "nif_emisor" in faltan
