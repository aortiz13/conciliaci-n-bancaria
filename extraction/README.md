# Servicio de extracción y validación (Python)

Paquete Python con la lógica de extracción y las **tools deterministas** del
MVP (PRD secciones 10 y 13). Pensado para desplegarse como funciones
serverless de Python en Vercel (Fase 2); por ahora contiene la lógica pura y
testable de la **Fase 1**.

## Contenido

| Módulo | Responsabilidad |
|--------|-----------------|
| `models.py` | Modelos pydantic (`ExtractedInvoice`, `InvoiceLine`, `TaxSubtotal`, `ReconCandidate`). |
| `validators.py` | `validate_nif` (mod-23), `validate_iban` (MOD-97), `validate_vat_arithmetic`. |
| `duplicates.py` | `detect_duplicate` / `find_duplicate` / `is_duplicate` (RF-15). |
| `routing.py` | `route_invoice` + `campos_faltantes` (enrutado por completitud/validaciones/confidence). |

Pendiente de la Fase 2: `extract_invoice` (LLM multimodal Gemini) y el `InvoiceRepo`
real contra Supabase.

## Desarrollo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"      # o: pip install -r requirements.txt pytest
pytest -q
```

## Notas de las validaciones

- **NIF/NIE/CIF**: DNI y NIE por letra de control mod-23; CIF por dígito/letra
  de control según el tipo de organización.
- **IBAN**: MOD-97 (ISO 13616) + comprobación de longitud por país.
- **IVA**: Σ bases por tipo ≈ base_total, Σ cuotas ≈ cuota_total, cuota de cada
  subtotal ≈ base×tipo, y base + cuota − IRPF ≈ total (con tolerancia por
  redondeos, 0,02 € por defecto).
