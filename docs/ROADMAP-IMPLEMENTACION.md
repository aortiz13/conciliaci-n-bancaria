# Roadmap de implementación del MVP

Desglose del MVP en fases incrementales. Cada fase deja el sistema en un estado
verificable. El alcance funcional completo está en [PRD.md](./PRD.md).

## Fase 0 — Fundaciones ✅ (en curso)

Base técnica sobre la que se monta todo el MVP.

- [x] Scaffold Next.js (App Router) + TypeScript + Tailwind.
- [x] Clientes Supabase: browser, server (SSR) y admin (`service_role`).
- [x] Middleware de refresco de sesión.
- [x] Plantilla `.env.example` con todas las integraciones.
- [x] Migraciones SQL del schema completo (sección 12 del PRD) con enums,
      índices por `tenant_id` y triggers `updated_at`.
- [x] Políticas RLS por membresía de tenant (+ helpers `is_tenant_member` /
      `is_tenant_admin`).
- [x] Bucket de Storage privado `invoices` con RLS por carpeta de tenant.
- [ ] **Pendiente:** provisionar proyecto Supabase real en región UE y aplicar
      migraciones (bloqueado por el límite de 2 proyectos free — requiere
      liberar un hueco desde el panel).
- [ ] Regenerar `src/lib/supabase/types.ts` desde el schema aplicado.

## Fase 1 — Validadores deterministas

Lógica pura, sin dependencias externas, con tests (RF-12 a RF-15).

- [ ] `validate_nif` — checksum NIF/NIE/CIF (mod-23).
- [ ] `validate_iban` — checksum IBAN (MOD-97).
- [ ] `validate_vat_arithmetic` — bases, cuotas por tipo, IRPF, total.
- [ ] `detect_duplicate` — emisor + nº/serie + total + fecha.
- [ ] `route_invoice` — enrutado por completitud + validaciones + confidence.

## Fase 2 — Ingesta + extracción

Captura por canal y registro estructurado (RF-1 a RF-11).

- [ ] Webhook ingest (tenant + proveedor, persistencia en Storage, encolado).
- [ ] Canal Telegram (grammY) con declaración de IA (RF-9).
- [ ] Canal email inbound (SendGrid Inbound Parse), alias por tenant.
- [ ] Cola durable (Inngest) con reintentos idempotentes.
- [ ] Servicio de extracción (Gemini multimodal) + confidence por campo.
- [ ] Alta de proveedor provisional en cuarentena por NIF.

## Fase 3 — App web de revisión

UI del equipo interno (RF-16, RF-17, RF-21, RF-25).

- [ ] Auth + selección de tenant + roles admin/operador.
- [ ] Listado filtrable de facturas + detalle con archivo embebido.
- [ ] Edición/recompletado de campos y re-validación.
- [ ] Cola de excepciones.

## Fase 4 — Conciliación

Motor factura ↔ extracto (RF-18 a RF-20).

- [ ] Parser Norma 43 + CSV/Excel (SheetJS) → movimientos normalizados.
- [ ] Generación y scoring de candidatos (importe/concepto/fecha/CIF).
- [ ] Escenarios 1:1, 1:N, N:1 y parciales; confirmación y match manual.

## Fase 5 — Dashboard, export, alertas y billing

Cierre del MVP (RF-22 a RF-28).

- [ ] Dashboard (totales/pendientes/conciliado).
- [ ] Export CSV/Excel para el asesor.
- [ ] Alertas de duplicados y vencimientos.
- [ ] Contador de uso por tenant + tope duro del plan Free.
- [ ] Log de auditoría conectado a los cambios de estado.

## Roadmap de producto (post-MVP)

Ver sección 15 del PRD: **V1** (open banking, WhatsApp, gestoría) ·
**V2** (e-factura B2B / XML) · **V3** (pagos + integración ERP, RF-29).
