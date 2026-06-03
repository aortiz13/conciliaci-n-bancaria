"""Validaciones deterministas (PRD RF-12 a RF-14, sección 13).

Lógica pura, sin dependencias externas:
  - validate_nif:  checksum NIF/NIE/CIF (mod-23 y control de CIF).
  - validate_iban: checksum IBAN (MOD-97).
  - validate_vat_arithmetic: coherencia de bases, cuotas e IRPF con el total.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import ExtractedInvoice

# ---------------------------------------------------------------------------
# NIF / NIE / CIF
# ---------------------------------------------------------------------------

# Letra de control del DNI/NIF y NIE (índice = nº mod 23).
_NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

# Letras de tipo de organización válidas en un CIF.
_CIF_ORG_LETTERS = "ABCDEFGHJNPQRSUVW"
# Letra de control alternativa del CIF (índice = dígito de control).
_CIF_CONTROL_LETTERS = "JABCDEFGHI"
# Tipos de organización cuyo control es siempre letra / siempre dígito.
_CIF_LETTER_ORGS = "PQSKNW"
_CIF_DIGIT_ORGS = "ABEH"


def _normalize(value: str) -> str:
    return re.sub(r"[\s\-\.]", "", value).upper()


def _validate_dni(doc: str) -> tuple[bool, Optional[str]]:
    """NIF de persona física: 8 dígitos + letra de control."""
    numero = int(doc[:8])
    esperada = _NIF_LETTERS[numero % 23]
    if doc[8] != esperada:
        return False, f"Letra de control incorrecta (esperada {esperada})"
    return True, None


def _validate_nie(doc: str) -> tuple[bool, Optional[str]]:
    """NIE: X/Y/Z + 7 dígitos + letra; el prefijo se mapea a 0/1/2."""
    prefijo = {"X": "0", "Y": "1", "Z": "2"}[doc[0]]
    numero = int(prefijo + doc[1:8])
    esperada = _NIF_LETTERS[numero % 23]
    if doc[8] != esperada:
        return False, f"Letra de control incorrecta (esperada {esperada})"
    return True, None


def _validate_cif(doc: str) -> tuple[bool, Optional[str]]:
    """CIF: letra de organización + 7 dígitos + control (dígito o letra)."""
    org = doc[0]
    central = doc[1:8]
    control = doc[8]

    suma = 0
    for i, ch in enumerate(central):
        n = int(ch)
        if i % 2 == 0:  # posiciones impares (1ª, 3ª, ...): se duplican
            doblado = n * 2
            suma += doblado // 10 + doblado % 10
        else:
            suma += n

    digito_control = (10 - (suma % 10)) % 10
    letra_control = _CIF_CONTROL_LETTERS[digito_control]

    if org in _CIF_LETTER_ORGS:
        ok = control == letra_control
    elif org in _CIF_DIGIT_ORGS:
        ok = control == str(digito_control)
    else:  # ambiguo: se admite dígito o letra
        ok = control in (str(digito_control), letra_control)

    if not ok:
        return False, (
            f"Control de CIF incorrecto (esperado {digito_control}"
            f"/{letra_control})"
        )
    return True, None


def validate_nif(nif: str) -> tuple[bool, Optional[str]]:
    """Checksum NIF/NIE/CIF (mod-23). Devuelve (valido, motivo_error)."""
    if not nif:
        return False, "NIF vacío"

    doc = _normalize(nif)
    if len(doc) != 9:
        return False, "Longitud inválida (deben ser 9 caracteres)"

    primero = doc[0]
    if primero.isdigit():
        return _validate_dni(doc)
    if primero in "XYZ":
        return _validate_nie(doc)
    if primero in _CIF_ORG_LETTERS:
        return _validate_cif(doc)
    return False, f"Carácter inicial inválido: {primero}"


# ---------------------------------------------------------------------------
# IBAN (MOD-97, ISO 13616)
# ---------------------------------------------------------------------------

# Longitudes oficiales por país (subconjunto habitual en facturación ES/UE).
_IBAN_LENGTHS = {
    "ES": 24, "FR": 27, "DE": 22, "IT": 27, "PT": 25, "NL": 18,
    "BE": 16, "GB": 22, "IE": 22, "LU": 20, "AT": 20, "CH": 21,
    "PL": 28, "SE": 24, "DK": 18, "FI": 18, "NO": 15, "AD": 24,
}


def validate_iban(iban: str) -> tuple[bool, Optional[str]]:
    """Checksum IBAN (MOD-97). Devuelve (valido, motivo_error)."""
    if not iban:
        return False, "IBAN vacío"

    code = _normalize(iban)
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]+", code):
        return False, "Formato IBAN inválido"

    pais = code[:2]
    esperada = _IBAN_LENGTHS.get(pais)
    if esperada is not None and len(code) != esperada:
        return False, f"Longitud incorrecta para {pais} (esperada {esperada})"

    # Reordenar: los 4 primeros caracteres al final.
    reordenado = code[4:] + code[:4]
    # Sustituir cada letra por dos dígitos (A=10 ... Z=35).
    numerico = "".join(
        str(ord(ch) - 55) if ch.isalpha() else ch for ch in reordenado
    )
    if int(numerico) % 97 != 1:
        return False, "Dígitos de control IBAN incorrectos (MOD-97)"
    return True, None


# ---------------------------------------------------------------------------
# Aritmética de IVA
# ---------------------------------------------------------------------------


def validate_vat_arithmetic(
    inv: ExtractedInvoice, tol: float = 0.02
) -> tuple[bool, list[str]]:
    """Coherencia aritmética de la factura.

    Comprueba (con tolerancia `tol` por redondeos):
      - Σ bases por tipo  ≈ base_total
      - Σ cuotas por tipo ≈ cuota_total
      - cuota de cada subtotal ≈ base * tipo / 100
      - Σ bases + Σ cuotas − IRPF ≈ total

    Devuelve (ok, errores).
    """
    errores: list[str] = []

    if inv.tax_subtotals:
        suma_bases = sum(s.base for s in inv.tax_subtotals)
        suma_cuotas = sum(s.cuota for s in inv.tax_subtotals)

        if abs(suma_bases - inv.base_total) > tol:
            errores.append(
                f"Σ bases ({suma_bases:.2f}) ≠ base_total ({inv.base_total:.2f})"
            )
        if abs(suma_cuotas - inv.cuota_total) > tol:
            errores.append(
                f"Σ cuotas ({suma_cuotas:.2f}) ≠ cuota_total "
                f"({inv.cuota_total:.2f})"
            )

        for s in inv.tax_subtotals:
            cuota_esperada = s.base * s.tipo_iva / 100.0
            if abs(s.cuota - cuota_esperada) > tol:
                errores.append(
                    f"Cuota del {s.tipo_iva}% ({s.cuota:.2f}) ≠ "
                    f"base×tipo ({cuota_esperada:.2f})"
                )
    else:
        suma_bases = inv.base_total
        suma_cuotas = inv.cuota_total

    total_calc = suma_bases + suma_cuotas - inv.irpf
    if abs(total_calc - inv.total) > tol:
        errores.append(
            f"base + cuota − IRPF ({total_calc:.2f}) ≠ total ({inv.total:.2f})"
        )

    return (len(errores) == 0), errores
