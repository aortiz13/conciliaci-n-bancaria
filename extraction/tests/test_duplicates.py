"""Tests de detección de duplicados."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from conciliacion_extraction.duplicates import (
    detect_duplicate,
    find_duplicate,
    is_duplicate,
)


@dataclass
class FakeInvoice:
    id: str
    nif_emisor: Optional[str]
    numero: Optional[str]
    total: Optional[float]
    fecha_expedicion: Optional[date]


_BASE = dict(
    nif_emisor="A58818501",
    numero="2026-001",
    total=121.0,
    fecha=date(2026, 1, 15),
)


def _existing(**kwargs) -> FakeInvoice:
    data = dict(
        id="inv-1",
        nif_emisor="A58818501",
        numero="2026-001",
        total=121.0,
        fecha_expedicion=date(2026, 1, 15),
    )
    data.update(kwargs)
    return FakeInvoice(**data)


def test_duplicado_exacto():
    assert is_duplicate(**_BASE, other=_existing())


def test_duplicado_ignora_mayusculas_y_espacios():
    other = _existing(nif_emisor="a58818501", numero=" 2026-001 ")
    assert is_duplicate(**_BASE, other=other)


def test_no_duplicado_distinto_numero():
    assert not is_duplicate(**_BASE, other=_existing(numero="2026-002"))


def test_no_duplicado_importe_fuera_de_tolerancia():
    assert not is_duplicate(**_BASE, other=_existing(total=121.5))


def test_no_duplicado_distinta_fecha():
    assert not is_duplicate(
        **_BASE, other=_existing(fecha_expedicion=date(2026, 2, 1))
    )


def test_find_duplicate_devuelve_id():
    existing = [_existing(id="otra", numero="x"), _existing(id="match")]
    assert find_duplicate(**_BASE, existing=existing) == "match"


def test_find_duplicate_sin_coincidencia():
    existing = [_existing(numero="x"), _existing(numero="y")]
    assert find_duplicate(**_BASE, existing=existing) is None


def test_detect_duplicate_con_repo():
    class Repo:
        def candidates_for_duplicate(self, tenant_id, nif_emisor, numero):
            assert tenant_id == "t1"
            return [_existing(id="dup")]

    result = detect_duplicate(
        "t1", _BASE["nif_emisor"], _BASE["numero"], _BASE["total"],
        _BASE["fecha"], repo=Repo(),
    )
    assert result == "dup"
