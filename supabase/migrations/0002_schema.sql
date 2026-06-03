-- 0002_schema.sql
-- Schema núcleo del MVP (sección 12 del PRD).
-- Multi-tenant: toda tabla de negocio lleva `tenant_id uuid` indexado.
-- RLS se habilita en 0003_rls.sql.

-- ---------------------------------------------------------------------------
-- Tipos enumerados
-- ---------------------------------------------------------------------------
create type public.membership_role as enum ('admin', 'operator');
create type public.supplier_status as enum ('provisional', 'activo', 'cuarentena');
create type public.channel_type    as enum ('telegram', 'email', 'phone');
create type public.invoice_status  as enum (
  'registrada', 'registrada_revision', 'escalada', 'conciliada', 'pagada'
);
create type public.statement_format as enum ('n43', 'csv', 'xlsx');
create type public.match_status    as enum ('propuesto', 'confirmado', 'rechazado', 'manual');
create type public.exception_type  as enum ('dato_faltante', 'match_ambiguo', 'ilegible');
create type public.exception_status as enum ('abierta', 'resuelta', 'descartada');
create type public.message_direction as enum ('in', 'out');
create type public.erp_type        as enum ('holded', 'a3erp', 'sage200', 'sage50');

-- ---------------------------------------------------------------------------
-- Trigger genérico de updated_at
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Planes y tenants
-- ---------------------------------------------------------------------------
create table public.plans (
  id            text primary key,                  -- free / starter / pro / business
  nombre        text not null,
  precio_mes    numeric(10,2) not null default 0,
  docs_incluidos integer not null,
  extra_doc     numeric(10,4),                     -- null en free
  tope_duro     boolean not null default false     -- free bloquea al superar
);

insert into public.plans (id, nombre, precio_mes, docs_incluidos, extra_doc, tope_duro) values
  ('free',     'Free',     0,  10,   null,  true),
  ('starter',  'Starter',  19, 150,  0.15,  false),
  ('pro',      'Pro',      39, 400,  0.12,  false),
  ('business', 'Business', 79, 1000, 0.10,  false);

create table public.tenants (
  id          uuid primary key default gen_random_uuid(),
  nombre      text not null,
  nif         text,
  plan_id     text not null references public.plans(id) default 'free',
  email_alias text unique,                          -- alias inbound por tenant
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create trigger trg_tenants_updated before update on public.tenants
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Usuarios y membresías (Auth)
-- ---------------------------------------------------------------------------
-- Perfil espejo de auth.users (la fuente de verdad de credenciales es auth).
create table public.users (
  id         uuid primary key references auth.users(id) on delete cascade,
  email      text not null,
  created_at timestamptz not null default now()
);

create table public.memberships (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  user_id    uuid not null references public.users(id) on delete cascade,
  role       public.membership_role not null default 'operator',
  created_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);
create index idx_memberships_tenant on public.memberships(tenant_id);
create index idx_memberships_user   on public.memberships(user_id);

-- ---------------------------------------------------------------------------
-- Proveedores e identidades de canal
-- ---------------------------------------------------------------------------
create table public.suppliers (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  nombre     text,
  nif        text,
  iban       text,
  estado     public.supplier_status not null default 'provisional',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_suppliers_tenant on public.suppliers(tenant_id);
create index idx_suppliers_nif     on public.suppliers(tenant_id, nif);
create trigger trg_suppliers_updated before update on public.suppliers
  for each row execute function public.set_updated_at();

create table public.channel_identities (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  supplier_id uuid not null references public.suppliers(id) on delete cascade,
  tipo        public.channel_type not null,
  valor       text not null,                       -- username / email / teléfono
  created_at  timestamptz not null default now(),
  unique (tenant_id, tipo, valor)
);
create index idx_channel_identities_tenant   on public.channel_identities(tenant_id);
create index idx_channel_identities_supplier on public.channel_identities(supplier_id);

-- ---------------------------------------------------------------------------
-- Documentos (archivo original en Storage)
-- ---------------------------------------------------------------------------
create table public.documents (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  storage_path text not null,
  mime         text,
  hash         text,                               -- para deduplicación/idempotencia
  origen_canal public.channel_type,
  created_at   timestamptz not null default now()
);
create index idx_documents_tenant on public.documents(tenant_id);
create index idx_documents_hash    on public.documents(tenant_id, hash);

-- ---------------------------------------------------------------------------
-- Facturas: cabecera + líneas + subtotales por tipo de IVA
-- ---------------------------------------------------------------------------
create table public.invoices (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        uuid not null references public.tenants(id) on delete cascade,
  supplier_id      uuid references public.suppliers(id) on delete set null,
  document_id      uuid references public.documents(id) on delete set null,
  serie            text,
  numero           text,
  fecha_expedicion date,
  fecha_operacion  date,
  nif_emisor       text,
  nif_receptor     text,
  base_total       numeric(14,2),
  cuota_total      numeric(14,2),
  irpf             numeric(14,2) not null default 0,  -- línea negativa
  total            numeric(14,2),
  estado           public.invoice_status not null default 'registrada_revision',
  confidence_global numeric(5,4),
  external_ref     text,                              -- V3: ref en ERP destino
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index idx_invoices_tenant   on public.invoices(tenant_id);
create index idx_invoices_estado   on public.invoices(tenant_id, estado);
create index idx_invoices_supplier on public.invoices(supplier_id);
create index idx_invoices_fecha    on public.invoices(tenant_id, fecha_expedicion);
-- Deduplicación: emisor + serie/número + total + fecha por tenant.
create unique index uq_invoices_dedupe
  on public.invoices(tenant_id, nif_emisor, serie, numero, total, fecha_expedicion)
  where nif_emisor is not null and numero is not null;
create trigger trg_invoices_updated before update on public.invoices
  for each row execute function public.set_updated_at();

create table public.invoice_lines (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  invoice_id  uuid not null references public.invoices(id) on delete cascade,
  descripcion text,
  cantidad    numeric(14,4),
  precio_unit numeric(14,4),
  importe     numeric(14,2),
  tipo_iva    smallint check (tipo_iva in (0, 4, 10, 21)),
  confidence  numeric(5,4)
);
create index idx_invoice_lines_tenant  on public.invoice_lines(tenant_id);
create index idx_invoice_lines_invoice on public.invoice_lines(invoice_id);

create table public.invoice_tax_subtotals (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  invoice_id uuid not null references public.invoices(id) on delete cascade,
  tipo_iva   smallint not null check (tipo_iva in (0, 4, 10, 21)),
  base       numeric(14,2) not null,
  cuota      numeric(14,2) not null,
  unique (invoice_id, tipo_iva)
);
create index idx_invoice_tax_subtotals_tenant  on public.invoice_tax_subtotals(tenant_id);
create index idx_invoice_tax_subtotals_invoice on public.invoice_tax_subtotals(invoice_id);

-- ---------------------------------------------------------------------------
-- Extracto bancario: statements + movimientos normalizados
-- ---------------------------------------------------------------------------
create table public.bank_statements (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  formato      public.statement_format not null,
  fichero_path text,
  periodo_desde date,
  periodo_hasta date,
  created_at   timestamptz not null default now()
);
create index idx_bank_statements_tenant on public.bank_statements(tenant_id);

create table public.bank_movements (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  statement_id uuid not null references public.bank_statements(id) on delete cascade,
  fecha        date not null,
  importe      numeric(14,2) not null,
  concepto     text,
  contrapartida text,
  created_at   timestamptz not null default now()
);
create index idx_bank_movements_tenant    on public.bank_movements(tenant_id);
create index idx_bank_movements_statement on public.bank_movements(statement_id);
create index idx_bank_movements_fecha     on public.bank_movements(tenant_id, fecha);
create index idx_bank_movements_importe   on public.bank_movements(tenant_id, importe);
-- Índice trigram para matching fuzzy de concepto.
create index idx_bank_movements_concepto_trgm
  on public.bank_movements using gin (concepto extensions.gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- Conciliación: matches + links N:M
-- ---------------------------------------------------------------------------
create table public.reconciliation_matches (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  tipo            text not null check (tipo in ('1:1', '1:N', 'N:1', 'parcial')),
  score           numeric(5,4),
  estado          public.match_status not null default 'propuesto',
  importe_asignado numeric(14,2),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index idx_recon_matches_tenant on public.reconciliation_matches(tenant_id);
create index idx_recon_matches_estado on public.reconciliation_matches(tenant_id, estado);
create trigger trg_recon_matches_updated before update on public.reconciliation_matches
  for each row execute function public.set_updated_at();

create table public.match_links (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  match_id    uuid not null references public.reconciliation_matches(id) on delete cascade,
  invoice_id  uuid not null references public.invoices(id) on delete cascade,
  movement_id uuid not null references public.bank_movements(id) on delete cascade,
  unique (match_id, invoice_id, movement_id)
);
create index idx_match_links_tenant   on public.match_links(tenant_id);
create index idx_match_links_match    on public.match_links(match_id);
create index idx_match_links_invoice  on public.match_links(invoice_id);
create index idx_match_links_movement on public.match_links(movement_id);

-- ---------------------------------------------------------------------------
-- Cola de excepciones
-- ---------------------------------------------------------------------------
create table public.exceptions_queue (
  id         uuid primary key default gen_random_uuid(),
  tenant_id  uuid not null references public.tenants(id) on delete cascade,
  tipo       public.exception_type not null,
  ref_id     uuid not null,                         -- invoice_id o match_id
  motivo     text,
  estado     public.exception_status not null default 'abierta',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index idx_exceptions_tenant on public.exceptions_queue(tenant_id);
create index idx_exceptions_estado on public.exceptions_queue(tenant_id, estado);
create trigger trg_exceptions_updated before update on public.exceptions_queue
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Conversaciones del bot
-- ---------------------------------------------------------------------------
create table public.conversations (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null references public.tenants(id) on delete cascade,
  supplier_id uuid references public.suppliers(id) on delete set null,
  canal       public.channel_type not null,
  created_at  timestamptz not null default now()
);
create index idx_conversations_tenant on public.conversations(tenant_id);

create table public.messages (
  id              uuid primary key default gen_random_uuid(),
  tenant_id       uuid not null references public.tenants(id) on delete cascade,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  direccion       public.message_direction not null,
  contenido       text,
  intento         smallint not null default 1,      -- nº de intento (3 → escala)
  created_at      timestamptz not null default now()
);
create index idx_messages_tenant       on public.messages(tenant_id);
create index idx_messages_conversation on public.messages(conversation_id);

-- ---------------------------------------------------------------------------
-- Uso (billing) y auditoría
-- ---------------------------------------------------------------------------
create table public.usage_counters (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    uuid not null references public.tenants(id) on delete cascade,
  periodo      text not null,                        -- 'YYYY-MM'
  docs_count   integer not null default 0,
  extras_count integer not null default 0,
  updated_at   timestamptz not null default now(),
  unique (tenant_id, periodo)
);
create index idx_usage_counters_tenant on public.usage_counters(tenant_id);
create trigger trg_usage_counters_updated before update on public.usage_counters
  for each row execute function public.set_updated_at();

-- Auditoría inmutable: sin updates ni deletes (se fuerza vía RLS en 0003).
create table public.audit_log (
  id        uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  actor     text,                                    -- user_id, 'system', 'bot'
  accion    text not null,
  entidad   text,
  antes     jsonb,
  despues   jsonb,
  ts        timestamptz not null default now()
);
create index idx_audit_log_tenant on public.audit_log(tenant_id);
create index idx_audit_log_ts      on public.audit_log(tenant_id, ts);

-- ---------------------------------------------------------------------------
-- Conexiones ERP (opcional · V3)
-- ---------------------------------------------------------------------------
create table public.erp_connections (
  id                  uuid primary key default gen_random_uuid(),
  tenant_id           uuid not null references public.tenants(id) on delete cascade,
  erp_type            public.erp_type not null,
  credenciales_cifradas text,                        -- cifradas en reposo
  estado              text not null default 'inactiva',
  ultima_sync         timestamptz,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  unique (tenant_id, erp_type)
);
create index idx_erp_connections_tenant on public.erp_connections(tenant_id);
create trigger trg_erp_connections_updated before update on public.erp_connections
  for each row execute function public.set_updated_at();
