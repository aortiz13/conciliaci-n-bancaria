# Roadmap de implementación del MVP

Desglose del MVP en fases incrementales. Cada fase deja el sistema en un estado
verificable. El alcance funcional completo está en [PRD.md](./PRD.md).

## Fase 0 — Fundaciones ✅ (completada)

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
- [x] Migraciones aplicadas al proyecto Supabase `wnohtrqnhubqlantpmff`
      (región `eu-central-1`, UE) en el esquema dedicado `conciliacion`,
      aislado de la otra app del proyecto (que vive en `public`).
- [x] Clientes Supabase apuntando al esquema `conciliacion` por defecto.
- [x] Esquema `conciliacion` expuesto en la API y verificado vía REST
      (PostgREST responde y RLS bloquea al rol anónimo).
- [x] `src/lib/supabase/types.ts` con los tipos del esquema `conciliacion`
      (escritos a mano; el generador del MCP solo emite `public`).

## Fase 1 — Validadores deterministas ✅ (completada)

Lógica pura en Python (pydantic), sin dependencias externas, con tests
(`extraction/`, RF-12 a RF-15). 40 tests en verde.

- [x] `validate_nif` — checksum NIF/NIE/CIF (mod-23 + control de CIF).
- [x] `validate_iban` — checksum IBAN (MOD-97) + longitud por país.
- [x] `validate_vat_arithmetic` — bases, cuotas por tipo, IRPF, total.
- [x] `detect_duplicate` — emisor + nº + total + fecha (con `repo` inyectable).
- [x] `route_invoice` — enrutado por completitud + validaciones + confidence.
- [ ] **Fase 2:** `extract_invoice` (LLM multimodal) y `InvoiceRepo` real
      contra Supabase.

## Fase 2 — Ingesta + extracción ✅ (código completo; faltan claves)

Captura por canal y registro estructurado (RF-1 a RF-11). Código listo,
leyendo credenciales de entorno (a rellenar en `.env`).

- [x] Webhook ingest (persistencia en Storage + `documents`, encolado a Inngest):
      `src/lib/ingest/` (documents, tenant, suppliers).
- [x] Canal Telegram (grammY) con declaración de IA (RF-9):
      `src/lib/telegram/bot.ts` + `src/app/api/ingest/telegram/route.ts`.
- [x] Canal email inbound (SendGrid Inbound Parse), alias por tenant:
      `src/app/api/ingest/email/route.ts`.
- [x] Cola durable (Inngest) con reintentos idempotentes:
      `src/lib/inngest/*` + `src/app/api/inngest/route.ts`.
- [x] Servicio de extracción (Gemini multimodal) + confidence por campo:
      `extraction/.../extraction.py` + `api/extract.py` (Vercel Python).
- [x] Pipeline extract→validar→dedupe→enrutar→persistir (`pipeline.py`,
      `repo.py`) con tests (extractor y repo falsos).
- [x] Alta de proveedor provisional por NIF (`SupabaseRepo.find_or_create_supplier`).
- [x] Contador de uso atómico vía RPC `increment_usage` (migración 0006).
- [ ] **Pendiente (claves):** `TELEGRAM_BOT_TOKEN`, credenciales Vertex AI,
      `SENDGRID_INBOUND_SECRET`, claves Inngest; registrar el webhook de
      Telegram y el Inbound Parse de SendGrid.
- [ ] **Pendiente:** envío de repreguntas/escalado al proveedor por el canal
      (flujo B, 3 intentos) — la base (estado/excepciones) ya queda escrita.

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
