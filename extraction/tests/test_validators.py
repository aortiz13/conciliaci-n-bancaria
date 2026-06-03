"""Tests de las validaciones deterministas (NIF/NIE/CIF, IBAN, IVA)."""

from datetime import date

import pytest

from conciliacion_extraction.models import ExtractedInvoice, TaxSubtotal
from conciliacion_extraction.validators import (
    validate_iban,
    validate_nif,
    validate_vat_arithmetic,
)


# --- NIF / NIE / CIF -------------------------------------------------------


@pytest.mark.parametrize(
    "nif",
    [
        "12345678Z",       # DNI válido
        "12345678-Z",      # con separador
        "x1234567l",       # NIE válido en minúsculas
        "A58818501",       # CIF con control numérico
        "P1234567D",       # CIF con control de letra (organismo público)
    ],
)
def test_nif_validos(nif):
    ok, motivo = validate_nif(nif)
    assert ok, motivo


@pytest.mark.parametrize(
    "nif",
    [
        "12345678A",   # letra de control incorrecta
        "X1234567Z",   # NIE con letra incorrecta
        "A58818502",   # CIF con control incorrecto
        "1234567Z",    # longitud inválida
        "",            # vacío
        "ÑÑÑÑÑÑÑÑÑ",   # caracteres no válidos
    ],
)
def test_nif_invalidos(nif):
    ok, motivo = validate_nif(nif)
    assert not ok
    assert motivo


# --- IBAN ------------------------------------------------------------------


@pytest.mark.parametrize(
    "iban",
    [
        "ES9121000418450200051332",        # España (canónico)
        "ES91 2100 0418 4502 0005 1332",   # con espacios
        "DE89370400440532013000",          # Alemania
    ],
)
def test_iban_validos(iban):
    ok, motivo = validate_iban(iban)
    assert ok, motivo


@pytest.mark.parametrize(
    "iban",
    [
        "ES9121000418450200051333",   # dígito de control roto
        "ES911234",                   # longitud incorrecta para ES
        "1234567890",                 # formato inválido
        "",                           # vacío
    ],
)
def test_iban_invalidos(iban):
    ok, motivo = validate_iban(iban)
    assert not ok
    assert motivo


# --- Aritmética de IVA -----------------------------------------------------


def _inv(**kwargs) -> ExtractedInvoice:
    base = dict(
        numero="A-1",
        fecha_expedicion=date(2026, 1, 15),
        nif_emisor="A58818501",
        base_total=100.0,
        cuota_total=21.0,
        irpf=0.0,
        total=121.0,
        tax_subtotals=[TaxSubtotal(tipo_iva=21, base=100.0, cuota=21.0)],
        confidence_global=0.95,
    )
    base.update(kwargs)
    return ExtractedInvoice(**base)


def test_vat_simple_ok():
    ok, errores = validate_vat_arithmetic(_inv())
    assert ok, errores


def test_vat_multi_iva_ok():
    inv = _inv(
        base_total=150.0,
        cuota_total=26.0,
        total=176.0,
        tax_subtotals=[
            TaxSubtotal(tipo_iva=21, base=100.0, cuota=21.0),
            TaxSubtotal(tipo_iva=10, base=50.0, cuota=5.0),
        ],
    )
    ok, errores = validate_vat_arithmetic(inv)
    assert ok, errores


def test_vat_con_irpf_ok():
    # IRPF del 15% sobre la base: total = 100 + 21 - 15 = 106.
    inv = _inv(irpf=15.0, total=106.0)
    ok, errores = validate_vat_arithmetic(inv)
    assert ok, errores


def test_vat_tolerancia_redondeo():
    # Desvío de 1 céntimo dentro de la tolerancia por defecto (0,02).
    inv = _inv(total=121.01)
    ok, _ = validate_vat_arithmetic(inv)
    assert ok


def test_vat_total_incoherente():
    inv = _inv(total=200.0)
    ok, errores = validate_vat_arithmetic(inv)
    assert not ok
    assert any("total" in e for e in errores)


def test_vat_cuota_subtotal_incoherente():
    inv = _inv(tax_subtotals=[TaxSubtotal(tipo_iva=21, base=100.0, cuota=10.0)])
    ok, errores = validate_vat_arithmetic(inv)
    assert not ok
    assert errores


def test_vat_suma_bases_no_cuadra():
    inv = _inv(
        base_total=200.0,
        tax_subtotals=[TaxSubtotal(tipo_iva=21, base=100.0, cuota=21.0)],
    )
    ok, errores = validate_vat_arithmetic(inv)
    assert not ok
    assert any("bases" in e for e in errores)
