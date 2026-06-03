# PRD — Plataforma SaaS de Recepción Conversacional y Conciliación de Facturas

## 1. Metadata

| Campo | Valor |
|-------|-------|
| Producto | (nombre comercial) `[PENDIENTE]` |
| Versión PRD | 1.1 (MVP) |
| Fecha | 2026-06-03 |
| Autor | `[PENDIENTE: autor]` |
| Estado | Borrador para validación |
| Mercado | España (PYMES, facturación ~1M€/año) |

---

## 2. Resumen ejecutivo

Plataforma SaaS multi-tenant que permite a una PYME pagadora centralizar la recepción de las facturas de todos sus proveedores mediante un bot conversacional (Telegram + email inbound): el proveedor envía su factura (PDF o foto), el bot la captura, extrae los datos con un LLM multimodal, los valida (checksum de NIF/IBAN, aritmética de IVA) y los registra estructuradamente; el equipo interno revisa las facturas desde una app web y las concilia contra el extracto bancario cargado manualmente (Norma 43/CSV/Excel), con una cola de excepciones para los casos ambiguos. El MVP es un sistema autónomo sin integración con ERP, sin open banking y sin emisión de facturas (lo que lo deja fuera del scope de Verifactu). Como capa **opcional y posterior** (V3) se contempla la sincronización de las facturas conciliadas hacia el software contable/ERP del cliente vía API, sin alterar el core de captura + conciliación.

---

## 3. Problema y oportunidad

**Problema.** Las PYMES españolas reciben facturas de sus proveedores por canales dispersos (email, papel, WhatsApp, mano), las teclean manualmente y las concilian a ojo contra el banco. Es lento, caro y propenso a error: coste medio por factura ~12,88 $ y tiempo de procesamiento muy superior a las 24h en empresas no optimizadas (Ardent Partners 2025).

**Oportunidad — la ventana 2026-2028.** La factura electrónica B2B será obligatoria en formato estructurado EN16931 (Ley 18/2022 + RD 238/2026, BOE 31-mar-2026), con arranque escalonado proyectado ~Oct 2027 (>8M€) / ~Oct 2028 (resto) tras la Orden Ministerial pendiente. Durante 2026-2028 conviven el PDF y el XML: existe demanda inmediata de captura mixta. El PDF dejará de ser factura B2B válida, por lo que **el OCR de PDFs es un canal de ingesta durable pero menguante**. El valor defendible a largo plazo no está en el OCR sino en: (a) el motor de conciliación agnóstico al formato, (b) la futura conectividad de e-factura (FACeB2B / SPFE / plataforma privada), y (c) la capa de validación y compliance. La estrategia de producto es capturar los "gap years" con ingesta mixta y migrar el valor hacia conciliación + conectividad. La integración con ERP (sección 8, RF-29; sección 15, V3) es **palanca comercial opcional**, no núcleo: convierte la plataforma en front-end de captura que escribe facturas recibidas en la contabilidad del cliente.

---

## 4. Usuarios y roles

| Actor | Quién es | Relación con el producto | Dónde opera |
|-------|----------|--------------------------|-------------|
| **Empresa pagadora** | PYME ~1M€/año, ~30 proveedores, ~150 facturas/mes | **Cliente que paga** la suscripción | — |
| → Admin de cuenta | Responsable de la empresa pagadora | Gestiona suscripción, usuarios, configuración, alias de canal, conexión ERP (opcional) | App web |
| → Operador / Contabilidad | Administración interna | Revisa facturas, resuelve excepciones, concilia contra banco | App web |
| **Proveedor** | Emisor de facturas, poco digitalizado | **Usuario del bot**, no paga ni configura nada | Telegram / email |
| Plataforma (nosotros) | Proveedor del SaaS | Encargado del tratamiento (RGPD) | — |

Roles app web (MVP): **admin** y **operador**, con permisos separados. Sin rol "aprobador" en MVP. Sin multi-tenant anidado de gestoría (roadmap).

---

## 5. Objetivos y KPIs

| KPI | Definición | Target MVP | Target V1 | Benchmark |
|-----|-----------|-----------|-----------|-----------|
| Extracción automática (STP) | % facturas registradas sin intervención humana | 70% | 80% | best-in-class 49,2% |
| Precisión de campo (cabecera) | % campos de cabecera correctos | ≥97% | ≥98% | LLM multimodal 97-99% |
| Tiempo de procesamiento | Recepción → registro disponible | <2 min (p95) | <1 min | best-in-class 3,1 días |
| Tiempo a "factura conciliable" | Recepción → revisada y lista | <24h | <12h | best-in-class 3,1 días |
| Tasa de excepción | % facturas que requieren acción humana | <30% | <20% | media 22% / best 9% |
| Auto-conciliación | % movimientos casados automáticamente | 75% | 90% | producción realista ~90% |
| Coste de extracción/factura | Coste variable LLM + canal | <0,05 € | <0,03 € | best-in-class 2,88 $ total |
| Disponibilidad app web | Uptime mensual | 99,5% | 99,9% | — |

---

## 6. Casos de uso (user stories)

Las 5 son **MUST** para MVP.

| ID | Lado | User story |
|----|------|------------|
| US-1 | Proveedor | Como proveedor, envío mi factura por Telegram/email y recibo confirmación inmediata del bot de que se recibió. |
| US-2 | Proveedor | Como proveedor, si falta un dato el bot me lo indica (repregunta informativa) sin bloquear el registro. |
| US-3 | Empresa | Como operador, veo el listado filtrable de facturas capturadas con su estado y el archivo original de respaldo. |
| US-4 | Empresa | Como operador, concilio cada factura contra el movimiento bancario correspondiente. |
| US-5 | Empresa | Como operador, gestiono una cola de excepciones (matches ambiguos / datos dudosos) y los resuelvo manualmente. |

User stories de soporte (derivadas, también MVP): export CSV/Excel para el asesor (US-6), dashboard de totales/pendientes/conciliado (US-7), alertas de duplicados y vencimientos (US-8), gestión de roles admin/operador (US-9).

User story opcional (V3, no MVP): como admin, conecto mi software contable/ERP y la factura conciliada se vuelca como factura recibida sin re-teclear (US-10 → ver RF-29).

---

## 7. Flujos principales

### Flujo A — Ingesta + validación por bot (lado proveedor)

1. Proveedor envía PDF/foto al canal (Telegram o email del alias de la empresa pagadora).
2. El sistema identifica al proveedor por teléfono / username Telegram / email remitente. Si es **remitente nuevo desconocido** → crea proveedor **provisional** en cuarentena.
3. Se almacena el archivo en Supabase Storage (bucket privado del tenant).
4. El LLM multimodal extrae cabecera + líneas + subtotales de impuesto por tipo + totales, con confidence score por campo.
5. Validaciones automáticas: checksum NIF/CIF (mod-23), checksum IBAN (MOD-97), aritmética de IVA (Σ bases por tipo = base; Σ bases + Σ cuotas − IRPF = total).
6. **Decisión de enrutado:**
   - Todos los campos obligatorios presentes + validaciones OK + confidence alto → estado `registrada` (cuenta como STP).
   - Campo legible pero faltante/dudoso o confidence bajo → estado `registrada_revision` + entra a cola de excepciones. **Se registra igual (no bloquea).**
7. El bot responde: confirma recepción; si hay campo faltante, lo señala de forma informativa (modelo B, no bloqueante).

### Flujo B — Factura ilegible / no-factura / duplicado (lado proveedor)

1. La captura falla: foto ilegible, documento que no es factura, o duplicado detectado (mismo emisor + nº + importe).
2. El bot **rechaza** y pide reenvío indicando el motivo.
3. Hasta **3 intentos**. Al 3er fallo → escala a humano (estado `escalada`, notificación al operador).

### Flujo C — Manejo de dato faltante (lado empresa)

1. Operador abre cola de excepciones, ve la factura `registrada_revision` con campos marcados y el archivo de respaldo.
2. Corrige/completa el campo; el sistema re-ejecuta validaciones.
3. Factura pasa a `registrada` (lista para conciliar).

### Flujo D — Conciliación factura ↔ extracto bancario (lado empresa)

1. Operador carga extracto (Norma 43 / CSV / Excel). El parser normaliza a movimientos.
2. El motor genera candidatos por importe (con tolerancia para comisiones), concepto (fuzzy/semántico), fecha (ventana flexible) y CIF.
3. Escenarios: 1:1, 1:N, N:1, pagos parciales. Candidatos de alta confianza → match propuesto; baja confianza → cola de excepciones, sin bloquear el resto.
4. **Match confirmado** (auto o por operador) → factura pasa a `conciliada`; al verificarse el pago en el movimiento, a `pagada`; queda log de auditoría.
5. El operador puede **forzar un match manual** (incluido partir un pago 1:N a mano).
6. Aprendizaje: confirmaciones/rechazos ajustan el scoring futuro.

### Flujo E — Sincronización con ERP (opcional · V3, lado empresa)

1. Admin conecta el ERP/software contable del tenant (Holded, a3ERP, Sage 200…) desde configuración: credenciales o flujo OAuth según el destino.
2. Al pasar una factura a `conciliada`/`pagada` (o por acción manual del operador), el adaptador del ERP la crea como **factura recibida/de proveedor** vía API.
3. Se guarda el `external_ref` devuelto y se registra en `audit_log`. Fallo del ERP → reintento idempotente; no bloquea el estado interno.

---

## 8. Requerimientos funcionales

**Lado proveedor (bot)**

- **RF-1** — Recibir facturas vía Telegram Bot API (archivos hasta 20 MB).
- **RF-2** — Recibir facturas vía email inbound a un alias de dominio propio por tenant (adjuntos PDF/imagen hasta ~30 MB).
- **RF-3** — Aceptar PDF nativo, PDF escaneado, JPG, PNG. Tratar la foto de móvil como entrada de primera clase.
- **RF-4** — Identificar al proveedor por teléfono / username Telegram / email remitente.
- **RF-5** — Aceptar remitentes nuevos desconocidos creando proveedor provisional en cuarentena, auto-vinculado por NIF extraído.
- **RF-6** — Confirmar recepción al proveedor por el mismo canal.
- **RF-7** — Repreguntar de forma informativa por campos faltantes sin bloquear el registro (modelo B).
- **RF-8** — Rechazar capturas ilegibles/no-factura/duplicadas y pedir reenvío; escalar a humano tras 3 intentos.
- **RF-9** — El bot debe declarar que es una IA (EU AI Act Art. 50).

**Extracción y validación**

- **RF-10** — Extraer estructura: cabecera + array de líneas + array de subtotales de impuesto por tipo + totales (soportar multi-IVA).
- **RF-11** — Asignar confidence score por campo y enrutar baja confianza a revisión.
- **RF-12** — Validar checksum de NIF/NIE/CIF (mod-23).
- **RF-13** — Validar checksum de IBAN (MOD-97).
- **RF-14** — Validar aritmética de IVA (bases, cuotas por tipo, IRPF como línea negativa, total).
- **RF-15** — Detectar duplicados (emisor + nº/serie + importe + fecha).

**Lado empresa (app web)**

- **RF-16** — Listado filtrable de facturas (estado, proveedor, fecha, importe) con detalle y archivo de respaldo embebido.
- **RF-17** — Editar/completar campos de una factura y re-validar.
- **RF-18** — Cargar extracto bancario (Norma 43 / CSV / Excel) y normalizar movimientos.
- **RF-19** — Generar candidatos de conciliación (importe/concepto/fecha/CIF) para escenarios 1:1, 1:N, N:1 y parciales.
- **RF-20** — Confirmar, rechazar o forzar match manual; partir pagos 1:N.
- **RF-21** — Cola de excepciones para facturas dudosas y matches ambiguos.
- **RF-22** — Export CSV/Excel para el asesor contable.
- **RF-23** — Dashboard: totales, pendientes, conciliado vs no conciliado.
- **RF-24** — Alertas proactivas de duplicados y de vencimientos próximos.
- **RF-25** — Gestión de usuarios con roles admin / operador y permisos separados.

**Plataforma / billing**

- **RF-26** — Contador de documentos/mes por tenant con límite por plan y tarificación de extras.
- **RF-27** — Plan Free con tope duro de 10 docs/mes (bloquea al superar).
- **RF-28** — Log de auditoría inmutable de cambios de estado y conciliaciones.

**Integración ERP (opcional · V3, fuera de MVP)**

- **RF-29** — Sincronizar la factura `conciliada`/`pagada` hacia el ERP/software contable del tenant como **factura recibida/de proveedor**, vía capa de adaptadores configurable (un adaptador por ERP), con persistencia del `external_ref` y reintento idempotente ante fallo, sin bloquear el estado interno. Destinos prioritarios: Holded (API REST abierta), a3ERP/Wolters Kluwer (REST, requiere módulo Conectia del cliente), Sage 200 (REST/OAuth2). Sage 50 solo vía conector de terceros (no nativo).

---

## 9. Requerimientos no funcionales

| Categoría | Requisito |
|-----------|-----------|
| Latencia | Confirmación de recepción del bot <5 s. Extracción completa <2 min p95. App web TTFB <500 ms. |
| Disponibilidad | App web 99,5% mensual (MVP). Ingesta tolerante a caídas (reintentos durables, sin pérdida de mensajes). |
| Seguridad | RLS obligatorio en todas las tablas con `tenant_id`. `service_role` solo en backend. Buckets privados por tenant. Defense-in-depth: RLS + checks de aplicación. Credenciales de ERP cifradas en reposo, nunca expuestas al cliente. |
| Privacidad | Datos en región UE. Cifrado en tránsito (TLS) y en reposo. Borrado con bloqueo previo (LOPDGDD art. 32). |
| Escala | Diseñado para cientos de tenants × ~150 facturas/mes. `tenant_id` indexado en todas las tablas (políticas RLS sin índice → 2x-11x más lentas). |
| Observabilidad | Logs estructurados por tenant, métricas de extracción (confidence, STP rate), trazas de la cola async, alertas de fallo de extracción y de sincronización ERP. |
| Conservación | Facturas y archivos: 6 años (mercantil) ≥ 4 años (fiscal). |
| Resiliencia ingesta | Cola durable con reintentos idempotentes; un fallo de LLM no pierde el documento. La sincronización ERP (opcional) usa la misma cola durable. |

---

## 10. Arquitectura técnica

Multi-tenant sobre **Supabase** (Postgres + Auth + Storage) y **Vercel** (hosting app web + funciones serverless), con cola durable para el procesamiento asíncrono de extracción.

```
                    PROVEEDORES (poco digitalizados)
                    │
        ┌───────────┴───────────┐
        │                       │
   Telegram Bot API      Email inbound (alias por tenant)
   (grammY, ≤20MB)       (SendGrid Inbound Parse, ≤30MB)
        │                       │
        └───────────┬───────────┘
                    ▼
        ┌──────────────────────────────┐
        │  Webhook ingest (Vercel fn)   │  ── identifica tenant + proveedor
        │  - guarda archivo en Storage  │
        │  - encola job idempotente     │
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Cola durable (Inngest)       │  ── reintentos, sin pérdida
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Servicio de extracción       │  ── Vercel Python serverless
        │  - LLM multimodal (Gemini)    │
        │  - confidence por campo       │
        │  - validaciones NIF/IBAN/IVA  │
        └──────────────┬───────────────┘
                       ▼
   ┌─────────────────────────────────────────────────┐
   │                  SUPABASE                         │
   │  Postgres (RLS + tenant_id indexado)              │
   │  Storage (buckets privados por tenant)            │
   │  Auth (admin / operador)                          │
   └───────────────────┬───────────────────────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  App web (Next.js en Vercel)  │  ── EQUIPO INTERNO
        │  - listado / detalle          │
        │  - carga de extracto           │
        │  - motor de conciliación       │
        │  - cola de excepciones         │
        │  - dashboard / export / alertas│
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │  Capa de adaptadores ERP       │  ── OPCIONAL · V3
        │  (Holded / a3ERP / Sage 200)   │  ── push factura recibida vía API
        │  - interfaz ERPAdapter común   │  ── reintento idempotente (Inngest)
        └──────────────────────────────┘
```

**Componentes:**

- **Webhook ingest** (Vercel function, TS): recibe Telegram/email, resuelve tenant y proveedor, persiste archivo, encola.
- **Cola durable** (Inngest): orquesta extracción con reintentos idempotentes; aísla fallos de LLM de la recepción.
- **Servicio de extracción** (Vercel Python serverless): llama al LLM multimodal, calcula confidence, ejecuta validaciones (las tools de la sección 13).
- **Motor de conciliación** (función en Next.js/TS): genera y puntúa candidatos.
- **Parser de extracto**: Norma 43 (parser propio, formato fijo documentado) + CSV/Excel (SheetJS).
- **Supabase**: fuente de verdad, RLS, storage, auth.
- **App web** (Next.js App Router): UI del equipo interno.
- **Capa de adaptadores ERP** (opcional · V3, Next.js/TS): interfaz `ERPAdapter` común con una implementación por destino; se ejecuta sobre la cola durable para reintentos; aislada del core de captura/conciliación.

---

## 11. Stack tecnológico

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| Base de datos | **Supabase (Postgres)** | Obligatorio. Postgres gestionado + Auth + Storage + RLS nativo, ideal para multi-tenant con `tenant_id`. Región UE para RGPD. |
| Hosting | **Vercel** | Obligatorio. Despliegue Next.js, serverless TS y Python, edge. |
| App web | Next.js (App Router) + TypeScript + Tailwind | Integración nativa con Vercel y Supabase; SSR/RLS por usuario. |
| Bot Telegram | grammY (Node/TS) | Librería moderna y tipada para Telegram Bot API. Límite 20 MB asumido (cubre fotos y la mayoría de PDFs a este volumen). |
| Email inbound | SendGrid Inbound Parse | Sin coste por mensaje, alias por tenant, adjuntos ~30 MB, cero fricción de aprobación. |
| Extracción | **Gemini 2.5 Pro multimodal** (vía Vertex AI, región UE) | Mejor benchmark peer-reviewed (96,5% facturas limpias / 92,7% escaneadas, arXiv 2509.04469). Multimodal nativo para foto de móvil. Fallback a primer pase con Gemini 2.5 Flash para reducir coste, escalando a Pro en confidence bajo. |
| Validación/tools | Python serverless (Vercel) | Validaciones deterministas (NIF/IBAN/IVA) en Python tipado; contrato de la sección 13. |
| Orquestación async | Inngest | Workflows durables con reintentos; evita timeouts de funciones serverless en la extracción y en la sincronización ERP. |
| Parser extracto | Parser propio Norma 43 + SheetJS (xlsx/csv) | Norma 43 es formato fijo bien documentado; SheetJS cubre Excel/CSV. |
| Conciliación fuzzy | Postgres `pg_trgm` + embeddings opcionales | Matching de concepto por similitud sin servicios externos en MVP. |
| Conector ERP (opcional · V3) | Adaptadores REST: Holded (API key/Bearer), a3ERP/WK (OAuth WK Account + Conectia), Sage 200 (OAuth2) | APIs públicas existentes; Holded es la de menor fricción (REST/JSON, sin rate limit). Sage 50 requiere conector de terceros (Hyperext/nubyhub/Chift). |

`[PENDIENTE]` — confirmar región UE y DPA de Vertex AI / proveedor LLM antes de producción.

`[PENDIENTE]` — confirmar disponibilidad en producción de Holded API v2 y DPA de cada ERP destino antes de habilitar RF-29.

---

## 12. Schema de base de datos (Supabase / Postgres)

Todas las tablas con `tenant_id uuid` indexado y RLS por membresía del tenant.

| Tabla | Propósito | Campos clave |
|-------|-----------|--------------|
| `tenants` | Empresa pagadora | id, nombre, nif, plan_id, email_alias |
| `users` | Cuentas Auth | id (auth.uid), email |
| `memberships` | Usuario↔tenant + rol | tenant_id, user_id, role (`admin`/`operator`) |
| `suppliers` | Proveedores | tenant_id, nombre, nif, iban, estado (`provisional`/`activo`/`cuarentena`) |
| `channel_identities` | Identidades de canal → proveedor | tenant_id, supplier_id, tipo (`telegram`/`email`/`phone`), valor |
| `documents` | Archivo original | tenant_id, storage_path, mime, hash, origen_canal |
| `invoices` | Cabecera de factura | tenant_id, supplier_id, document_id, serie, numero, fecha_expedicion, fecha_operacion, nif_emisor, nif_receptor, base_total, cuota_total, irpf, total, estado (`registrada`/`registrada_revision`/`escalada`/`conciliada`/`pagada`), confidence_global, external_ref (opcional · V3) |
| `invoice_lines` | Líneas de detalle | invoice_id, descripcion, cantidad, precio_unit, importe, tipo_iva, confidence |
| `invoice_tax_subtotals` | Subtotal por tipo de IVA | invoice_id, tipo_iva (21/10/4/0), base, cuota |
| `bank_statements` | Extracto cargado | tenant_id, formato (`n43`/`csv`/`xlsx`), fichero_path, periodo |
| `bank_movements` | Movimiento normalizado | tenant_id, statement_id, fecha, importe, concepto, contrapartida |
| `reconciliation_matches` | Match factura↔movimiento | tenant_id, tipo (`1:1`/`1:N`/`N:1`/`parcial`), score, estado (`propuesto`/`confirmado`/`rechazado`/`manual`), importe_asignado |
| `match_links` | Relación N:M factura↔movimiento | match_id, invoice_id, movement_id |
| `exceptions_queue` | Excepciones | tenant_id, tipo (`dato_faltante`/`match_ambiguo`/`ilegible`), ref_id, motivo, estado |
| `conversations` | Hilo de bot por proveedor | tenant_id, supplier_id, canal |
| `messages` | Mensajes del hilo | conversation_id, direccion, contenido, intento |
| `usage_counters` | Conteo docs/mes | tenant_id, periodo, docs_count, extras_count |
| `audit_log` | Auditoría inmutable | tenant_id, actor, accion, entidad, antes, despues, ts |
| `erp_connections` (opcional · V3) | Conexión ERP por tenant | tenant_id, erp_type (`holded`/`a3erp`/`sage200`/`sage50`), credenciales_cifradas, estado, ultima_sync |

---

## 13. Tools del agente (firmas Python tipadas)

```python
from typing import Literal, Optional, Protocol
from datetime import date
from pydantic import BaseModel

class TaxSubtotal(BaseModel):
    tipo_iva: Literal[21, 10, 4, 0]
    base: float
    cuota: float

class InvoiceLine(BaseModel):
    descripcion: str
    cantidad: float
    precio_unit: float
    importe: float
    tipo_iva: Literal[21, 10, 4, 0]
    confidence: float

class ExtractedInvoice(BaseModel):
    serie: Optional[str]
    numero: str
    fecha_expedicion: date
    fecha_operacion: Optional[date]
    nif_emisor: str
    nif_receptor: Optional[str]
    base_total: float
    cuota_total: float
    irpf: float            # línea negativa (15% / 7%)
    total: float
    lines: list[InvoiceLine]
    tax_subtotals: list[TaxSubtotal]
    iban: Optional[str]
    confidence_global: float

def extract_invoice(file_bytes: bytes, mime: str) -> ExtractedInvoice:
    """Extrae estructura factura con LLM multimodal y confidence por campo."""

def validate_nif(nif: str) -> tuple[bool, Optional[str]]:
    """Checksum NIF/NIE/CIF (mod-23). Devuelve (valido, motivo_error)."""

def validate_iban(iban: str) -> tuple[bool, Optional[str]]:
    """Checksum IBAN (MOD-97)."""

def validate_vat_arithmetic(inv: ExtractedInvoice, tol: float = 0.02) -> tuple[bool, list[str]]:
    """Σ bases por tipo = base; Σ bases + Σ cuotas − IRPF = total. Devuelve (ok, errores)."""

def detect_duplicate(tenant_id: str, nif_emisor: str, numero: str,
                     total: float, fecha: date) -> Optional[str]:
    """Devuelve invoice_id si existe duplicado, si no None."""

class ReconCandidate(BaseModel):
    movement_id: str
    score: float
    tipo: Literal["1:1", "1:N", "N:1", "parcial"]
    razon: str

def find_reconciliation_candidates(
    invoice_id: str,
    importe_tol: float = 0.50,
    fecha_ventana_dias: int = 7,
) -> list[ReconCandidate]:
    """Candidatos por importe (tolerancia comisiones), concepto (fuzzy), fecha (ventana), CIF."""

def route_invoice(inv: ExtractedInvoice, validations: list[str]) -> Literal[
    "registrada", "registrada_revision", "escalada"]:
    """Enrutado por completitud + validaciones + confidence."""

# --- Integración ERP (opcional · V3) ---
class ERPAdapter(Protocol):
    """Interfaz común; una implementación por ERP destino."""
    def push_purchase_invoice(self, inv: ExtractedInvoice,
                              recon: Optional[ReconCandidate]) -> str:
        """Crea factura recibida/de proveedor en el ERP. Devuelve external_ref."""

# Implementaciones previstas:
#   HoldedAdapter  -> POST /invoicing/v1/documents/purchase  (header `key` v1 / Bearer v2)
#   A3ERPAdapter   -> REST a3factura, OAuth Wolters Kluwer Account (requiere Conectia)
#   Sage200Adapter -> REST Sage 200, OAuth2 (client_id/secret, programa partner)
#   Sage50Adapter  -> vía conector de terceros (Hyperext/nubyhub/Chift), no nativo
```

---

## 14. Estimación de costos por cliente/mes

Supuesto: tenant Starter, 150 facturas/mes. Costes fijos de infra amortizados entre ~50 tenants.

| Concepto | Coste unitario | A 150 facturas | Nota |
|----------|----------------|----------------|------|
| Extracción LLM (Flash 1er pase + Pro en ~20%) | ~0,02 €/factura | ~3,00 € | Multimodal región UE |
| Telegram Bot API | 0 € | 0 € | Gratis |
| Email inbound (SendGrid) | ~0 €/mensaje | ~0 € | Plan base cubre volumen |
| Supabase Pro | 25 $/mes ÷ ~50 tenants | ~0,50 € | Fijo amortizado |
| Vercel Pro | 20 $/mes ÷ ~50 tenants | ~0,40 € | Fijo amortizado |
| Storage (≈3 MB/factura) | despreciable | ~0,10 € | Incluido en Supabase |
| Inngest | tier base | ~0,20 € | A este volumen |
| Sincronización ERP (opcional · V3) | despreciable | ~0 € | Llamadas API; coste de oportunidad en desarrollo del adaptador, no marginal |
| **Coste variable total/cliente** | | **~4,20 €** | |

Plan Starter 19 €/mes → **margen bruto ~78%** a 150 facturas. Extra/doc 0,15 € (>7x coste marginal de ~0,02 €) protege el margen ante picos. A mayor volumen (Pro/Business) el margen sube por amortización fija.

| Plan | €/mes | Docs incluidos | Extra/doc |
|------|-------|----------------|-----------|
| Free | 0 | 10 (tope duro) | — |
| Starter | 19 | 150 | 0,15 € |
| Pro | 39 | 400 | 0,12 € |
| Business | 79 | 1.000 | 0,10 € |

Sin setup. Solo marca propia (sin white label). Sin tier gestoría (roadmap). La integración ERP (V3), si se monetiza, podría ofrecerse como add-on de plan superior; no afecta al coste variable del MVP.

---

## 15. Roadmap por fases

| Fase | Alcance | Valor estratégico |
|------|---------|-------------------|
| **MVP** | Ingesta Telegram + email, extracción multimodal, validación, app web de revisión + conciliación con extracto manual (N43/CSV/Excel), cola de excepciones, dashboard, export, alertas | Capturar "gap years" 2026-2028 |
| **V1** | Open banking / PSD2 para carga automática de movimientos → conciliación automática; canal WhatsApp Business Cloud API; tier gestoría multi-cliente | Subir auto-conciliación a ~90%, ampliar canal |
| **V2** | Conectividad e-factura B2B (ingesta XML Facturae/UBL; conexión FACeB2B/SPFE/plataforma privada) | Sobrevivir a la obsolescencia del PDF; valor defendible |
| **V3** | Módulo de pagos a proveedores + flujo de aprobaciones; **integración ERP/software contable vía API (RF-29): Holded, a3ERP/Wolters Kluwer, Sage 200; Sage 50 vía conector de terceros** | Cerrar el ciclo procure-to-pay; eliminar el re-tecleo en contabilidad y reforzar retención |

---

## 16. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Obsolescencia del OCR ante e-factura B2B obligatoria** | Alto / estratégico | Tratar el PDF como canal menguante; invertir el valor en conciliación agnóstica al formato y planificar V2 (ingesta XML + conectividad e-factura) ya en roadmap. |
| Spam/identidad por aceptar remitentes nuevos | Medio | Proveedores nuevos → estado `provisional` en cuarentena; rate-limit por canal; no se concilian hasta validación del operador. |
| Líneas de detalle con baja precisión | Medio | Confidence por campo; baja confianza → cola de revisión, no auto-aceptación. |
| Límite 20 MB de Telegram Bot API | Bajo | Email inbound (30 MB) como alternativa; aviso al proveedor si excede; servidor local Telegram en V1 si necesario. |
| DPA genérico sancionable por AEPD | Alto / legal | Contrato de encargo Art. 28 específico, con lista de subencargados (Supabase, Vercel, Vertex/LLM, SendGrid) y región UE. |
| Coste LLM se dispara con volumen | Medio | Pase en dos niveles (Flash→Pro); extra/doc tarificado >7x coste marginal; monitorización de coste por tenant. |
| Cliente que supere umbral SII (6,01M€) | Medio | Target definido <2M€; si entra un cliente grande, marcar `[PENDIENTE]` y evaluar SII (plazo 4 días hábiles) como feature aparte. |
| Pérdida de mensaje en ingesta | Alto | Cola durable Inngest con reintentos idempotentes; persistencia del archivo antes de procesar. |
| Dependencia de plan/módulo del cliente para la API del ERP (opcional · V3) | Medio | Holded API solo en planes de pago (no Free); a3ERP requiere módulo Conectia; Sage 50 sin API nativa. Validar requisitos del cliente antes de ofrecer RF-29; degradar a export CSV (RF-22) si no aplica. |
| Nuevo flujo de datos a un tercero al sincronizar con ERP (opcional · V3) | Medio / legal | Añadir el ERP destino como subencargado al Art. 28; sincronizar solo facturas recibidas (no emisión → no Verifactu); credenciales cifradas. |

---

## 17. Compliance

**RGPD**

- **Roles:** la plataforma es **encargado del tratamiento**; la empresa pagadora es **responsable**.
- **Contrato Art. 28** específico (no genérico), listando subencargados: Supabase, Vercel, Vertex AI/LLM, SendGrid. Datos preferentemente en **región UE**. Si se habilita RF-29, añadir el ERP destino (Holded, Wolters Kluwer, Sage…) como subencargado/flujo a tercero.
- **Base legal:** Art. 6(1)(c) obligación legal (conservación fiscal) + 6(1)(b) ejecución de contrato; 6(1)(f) interés legítimo para fines auxiliares, con test de ponderación.
- **Conservación:** 6 años (mercantil, art. 30 C.Com.) ≥ 4 años (fiscal, art. 66 LGT). Bloqueo previo al borrado (LOPDGDD art. 32).

**EU AI Act (Reg. 2024/1689)**

- El sistema de extracción **no es alto riesgo** (fuera de Anexo III).
- Riesgo limitado por la interfaz de bot → **Art. 50(1): el bot debe declarar que es una IA** (RF-9). Aplicable desde 2-ago-2026.
- Evitar scope-creep a scoring de solvencia de personas físicas (entraría en Anexo III).

**Verifactu — por qué el MVP queda fuera de scope**

- El producto **solo recibe y registra** facturas de terceros. Verifactu (RD 1007/2023) y el Reglamento de SIF aplican al software que **emite** facturas, no al que las recibe → **MVP fuera de scope**.
- Esto cambiaría si se añadiera emisión o auto-facturación (por eso "emisión" está en out of scope, sección 19). La sincronización ERP (RF-29) escribe facturas **recibidas** en la contabilidad del cliente, no emite → no activa Verifactu.
- Calendario de referencia (no aplica al MVP): usuarios obligados a Verifactu desde 1-ene-2027 (sociedades) / 1-jul-2027 (resto), RDL 15/2025.

**Factura válida (RD 1619/2012):** el validador exige nº/serie correlativo, fecha de expedición (y de operación si difiere), razón social + NIF emisor (siempre) y receptor (para deducir IVA), concepto, base imponible desglosada por tipo, cuota por tipo y total. IBAN no es legalmente obligatorio pero se captura por ser crítico para conciliar.

`[PENDIENTE]` — confirmar contra AEAT el recargo de equivalencia (~5,2/1,4/0,5%) antes de hardcodear sus tipos.

---

## 18. Criterios de aceptación MVP

- [ ] Un proveedor envía una factura por Telegram y recibe confirmación del bot en <5 s.
- [ ] Un proveedor envía una factura por email (alias del tenant) y queda registrada.
- [ ] El bot declara que es una IA.
- [ ] PDF nativo, PDF escaneado, JPG y PNG se procesan correctamente.
- [ ] Factura completa + validaciones OK → estado `registrada` sin intervención (cuenta como STP).
- [ ] Campo faltante → factura registrada igual + entra a cola de excepciones (no bloquea); el bot repregunta informativamente.
- [ ] Factura ilegible/no-factura/duplicado → rechazo y reenvío; escala tras 3 intentos.
- [ ] Validaciones NIF/CIF (mod-23), IBAN (MOD-97) y aritmética de IVA operativas.
- [ ] Extracción modela cabecera + líneas + subtotales por tipo de IVA + totales (multi-IVA).
- [ ] Remitente nuevo → proveedor provisional en cuarentena, auto-vinculado por NIF.
- [ ] Operador ve listado filtrable con archivo de respaldo y edita campos.
- [ ] Carga de extracto N43/CSV/Excel y normalización de movimientos.
- [ ] Motor de conciliación propone candidatos para 1:1, 1:N, N:1 y parciales.
- [ ] Operador confirma, rechaza y fuerza match manual; match confirmado → `conciliada/pagada` con log.
- [ ] Dashboard (totales/pendientes/conciliado), export CSV/Excel, alertas de duplicados y vencimientos.
- [ ] Roles admin/operador con permisos separados.
- [ ] RLS activo y verificado en todas las tablas con `tenant_id` indexado.
- [ ] Plan Free bloquea al superar 10 docs/mes; contador de uso por tenant.
- [ ] STP ≥70%, precisión cabecera ≥97%, procesamiento <2 min p95.

(RF-29 / integración ERP no forma parte de los criterios de aceptación del MVP; ver V3.)

---

## 19. Out of scope MVP

- Emisión de facturas (activaría Verifactu).
- Auto-facturación / emisión por cuenta del proveedor.
- Integración con ERP / software contable del cliente (→ V3, opcional, RF-29).
- Open banking / PSD2 (extracto se carga manualmente).
- Módulo de pago a proveedores y flujo de aprobaciones.
- Ingesta de XML Facturae/UBL (→ V2).
- WhatsApp como canal (→ V1).
- Tier de gestoría multi-cliente / multi-tenant anidado (→ roadmap).
- White label.
- SII (cliente target <umbral 6,01M€).

---

## 20. Anexos

### Glosario

| Término | Definición |
|---------|-----------|
| Empresa pagadora | PYME que paga la suscripción y recibe facturas de sus proveedores. |
| STP | Straight-through processing: factura registrada sin intervención humana. |
| Norma 43 / Cuaderno 43 | Formato estándar español de extracto bancario (CSB/AEB). |
| RLS | Row Level Security de Postgres; aísla datos por tenant. |
| Confidence score | Probabilidad de acierto por campo extraído; enruta a revisión. |
| Cola de excepciones | Bandeja de facturas/matches que requieren acción humana. |
| Verifactu | Sistema antifraude para software que **emite** facturas (RD 1007/2023). |
| e-factura B2B | Factura electrónica estructurada EN16931 obligatoria (Ley 18/2022 + RD 238/2026). |
| Factura recibida | Factura de proveedor que el cliente contabiliza como gasto; objeto del push al ERP (RF-29). |
| Conectia | Módulo de Wolters Kluwer que habilita el acceso API a a3ERP/a3 cloud. |

### Decisiones tomadas

| # | Decisión |
|---|----------|
| D1 | Target: PYME ~1M€/año, ~30 proveedores, ~150 facturas/mes, <umbral SII. |
| D2 | 1 cuenta = 1 empresa pagadora; sin multi-tenant anidado en MVP. |
| D3 | Roles: admin + operador, permisos separados. |
| D4 | Canales MVP: Telegram (primario) + email inbound (alias de dominio propio). WhatsApp a V1. |
| D5 | Bot acepta remitentes nuevos → proveedor provisional en cuarentena, auto-vinculado por NIF. |
| D6 | Dato faltante = registrar + marcar revisión (no bloquea); repregunta informativa. |
| D7 | Ilegible/no-factura/duplicado = rechazo, 3 intentos, luego escala. |
| D8 | Tipos MVP: PDF nativo/escaneado + foto JPG/PNG. XML a V2. |
| D9 | Conciliación: match confirmado → `conciliada/pagada`; operador puede forzar match manual. |
| D10 | Pricing: mensualidad + extra/doc, sin setup. Free 10 docs. Starter 19 / Pro 39 / Business 79 €. |
| D11 | Solo marca propia, sin white label, sin tier gestoría en MVP. |
| D12 | Stack: Supabase + Vercel obligatorios; extracción Gemini 2.5 multimodal región UE; Telegram grammY; email SendGrid; orquestación Inngest. |
| D13 | Integración ERP fuera de MVP, opcional en V3 (RF-29) vía capa de adaptadores; prioridad Holded > a3ERP > Sage 200; Sage 50 solo vía conector de terceros. Sincroniza solo facturas recibidas (no activa Verifactu). |

### Pendientes

| # | Pendiente |
|---|-----------|
| P1 | Nombre comercial y autor del PRD. |
| P2 | Perfil de primer cliente / canal de outreach (no definido aún). |
| P3 | Confirmar región UE y DPA del proveedor LLM (Vertex AI). |
| P4 | Confirmar tipos de recargo de equivalencia contra AEAT antes de hardcodear. |
| P5 | Revisar SII si entra un cliente >6,01M€. |
| P6 | (V3) Confirmar disponibilidad en producción de Holded API v2, requisitos de módulo Conectia en a3ERP y alta en programa partner de Sage 200; DPA de cada ERP destino antes de habilitar RF-29. |
