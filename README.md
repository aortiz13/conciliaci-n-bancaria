# Conciliación Bancaria — Recepción Conversacional y Conciliación de Facturas

Plataforma SaaS multi-tenant para que una PYME pagadora centralice la **recepción de facturas de sus proveedores** mediante un bot conversacional (Telegram + email inbound), las extraiga con un LLM multimodal, las valide (NIF/IBAN/IVA) y las **concilie contra el extracto bancario**, con una cola de excepciones para los casos ambiguos.

> **Estado:** fase de definición. Este repositorio contiene por ahora la documentación de producto (PRD). Aún no hay código de la aplicación.

## ¿Qué resuelve?

Las PYMES españolas reciben facturas por canales dispersos (email, papel, WhatsApp, mano), las teclean a mano y las concilian a ojo contra el banco. Esta plataforma automatiza la captura y la conciliación durante los "gap years" 2026-2028, antes de la obligatoriedad de la e-factura B2B estructurada.

## Alcance del MVP

- **Ingesta** vía Telegram (grammY) + email inbound (SendGrid Inbound Parse).
- **Extracción** con LLM multimodal (Gemini 2.5) con confidence por campo.
- **Validación** determinista: checksum NIF/CIF (mod-23), IBAN (MOD-97), aritmética de IVA.
- **App web** (Next.js) para revisión, edición y conciliación.
- **Conciliación** factura ↔ extracto bancario (Norma 43 / CSV / Excel), escenarios 1:1, 1:N, N:1 y parciales.
- **Cola de excepciones**, dashboard, export CSV/Excel y alertas.

Fuera del MVP: emisión de facturas, open banking, ingesta XML, WhatsApp e integración con ERP (ver roadmap en el PRD).

## Stack previsto

| Capa | Tecnología |
|------|------------|
| Base de datos / Auth / Storage | Supabase (Postgres + RLS, región UE) |
| Hosting | Vercel (Next.js + serverless TS/Python) |
| App web | Next.js (App Router) + TypeScript + Tailwind |
| Bot Telegram | grammY |
| Email inbound | SendGrid Inbound Parse |
| Extracción | Gemini 2.5 multimodal (Vertex AI) |
| Orquestación async | Inngest |

## Documentación

- [PRD completo](docs/PRD.md) — requisitos, arquitectura, schema de BD, compliance, roadmap y criterios de aceptación.

## Compliance (resumen)

- **RGPD:** la plataforma es encargado del tratamiento; datos en región UE; contrato Art. 28 con subencargados.
- **EU AI Act:** el bot declara que es una IA (Art. 50).
- **Verifactu:** fuera de scope — el producto solo **recibe** facturas, no las emite.
