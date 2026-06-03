-- 0003_rls.sql
-- Row Level Security por membresía de tenant (sección 9 del PRD).
-- Las funciones helper son SECURITY DEFINER para evitar recursión de RLS
-- al consultar `memberships` desde las propias políticas.

-- ---------------------------------------------------------------------------
-- Helpers de autorización
-- ---------------------------------------------------------------------------
create or replace function conciliacion.is_tenant_member(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = conciliacion, public
as $$
  select exists (
    select 1
    from conciliacion.memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = auth.uid()
  );
$$;

create or replace function conciliacion.is_tenant_admin(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = conciliacion, public
as $$
  select exists (
    select 1
    from conciliacion.memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = auth.uid()
      and m.role = 'admin'
  );
$$;

-- ---------------------------------------------------------------------------
-- Habilitar RLS en todas las tablas
-- ---------------------------------------------------------------------------
alter table conciliacion.plans                 enable row level security;
alter table conciliacion.tenants               enable row level security;
alter table conciliacion.users                 enable row level security;
alter table conciliacion.memberships           enable row level security;
alter table conciliacion.suppliers             enable row level security;
alter table conciliacion.channel_identities    enable row level security;
alter table conciliacion.documents             enable row level security;
alter table conciliacion.invoices              enable row level security;
alter table conciliacion.invoice_lines         enable row level security;
alter table conciliacion.invoice_tax_subtotals enable row level security;
alter table conciliacion.bank_statements       enable row level security;
alter table conciliacion.bank_movements        enable row level security;
alter table conciliacion.reconciliation_matches enable row level security;
alter table conciliacion.match_links           enable row level security;
alter table conciliacion.exceptions_queue      enable row level security;
alter table conciliacion.conversations         enable row level security;
alter table conciliacion.messages              enable row level security;
alter table conciliacion.usage_counters        enable row level security;
alter table conciliacion.audit_log             enable row level security;
alter table conciliacion.erp_connections       enable row level security;

-- ---------------------------------------------------------------------------
-- plans: catálogo de solo lectura para usuarios autenticados
-- ---------------------------------------------------------------------------
create policy plans_select on conciliacion.plans
  for select to authenticated using (true);

-- ---------------------------------------------------------------------------
-- tenants: miembros leen; admin actualiza
-- ---------------------------------------------------------------------------
create policy tenants_select on conciliacion.tenants
  for select to authenticated using (conciliacion.is_tenant_member(id));
create policy tenants_update on conciliacion.tenants
  for update to authenticated
  using (conciliacion.is_tenant_admin(id))
  with check (conciliacion.is_tenant_admin(id));

-- ---------------------------------------------------------------------------
-- users: cada usuario gestiona su propia fila
-- ---------------------------------------------------------------------------
create policy users_select on conciliacion.users
  for select to authenticated using (id = auth.uid());
create policy users_insert on conciliacion.users
  for insert to authenticated with check (id = auth.uid());
create policy users_update on conciliacion.users
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---------------------------------------------------------------------------
-- memberships: miembros del tenant leen; admin gestiona
-- ---------------------------------------------------------------------------
create policy memberships_select on conciliacion.memberships
  for select to authenticated using (conciliacion.is_tenant_member(tenant_id));
create policy memberships_admin_write on conciliacion.memberships
  for all to authenticated
  using (conciliacion.is_tenant_admin(tenant_id))
  with check (conciliacion.is_tenant_admin(tenant_id));

-- ---------------------------------------------------------------------------
-- Tablas operativas: CRUD completo para cualquier miembro (admin u operador)
-- ---------------------------------------------------------------------------
create policy suppliers_rw on conciliacion.suppliers
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy channel_identities_rw on conciliacion.channel_identities
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy documents_rw on conciliacion.documents
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy invoices_rw on conciliacion.invoices
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy invoice_lines_rw on conciliacion.invoice_lines
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy invoice_tax_subtotals_rw on conciliacion.invoice_tax_subtotals
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy bank_statements_rw on conciliacion.bank_statements
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy bank_movements_rw on conciliacion.bank_movements
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy reconciliation_matches_rw on conciliacion.reconciliation_matches
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy match_links_rw on conciliacion.match_links
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy exceptions_queue_rw on conciliacion.exceptions_queue
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy conversations_rw on conciliacion.conversations
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

create policy messages_rw on conciliacion.messages
  for all to authenticated
  using (conciliacion.is_tenant_member(tenant_id))
  with check (conciliacion.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- usage_counters: miembros leen; escritura solo backend (service_role)
-- ---------------------------------------------------------------------------
create policy usage_counters_select on conciliacion.usage_counters
  for select to authenticated using (conciliacion.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- audit_log: miembros leen e insertan (append-only); sin update/delete
-- ---------------------------------------------------------------------------
create policy audit_log_select on conciliacion.audit_log
  for select to authenticated using (conciliacion.is_tenant_member(tenant_id));
create policy audit_log_insert on conciliacion.audit_log
  for insert to authenticated with check (conciliacion.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- erp_connections: solo admin (contiene credenciales)
-- ---------------------------------------------------------------------------
create policy erp_connections_admin on conciliacion.erp_connections
  for all to authenticated
  using (conciliacion.is_tenant_admin(tenant_id))
  with check (conciliacion.is_tenant_admin(tenant_id));

-- ---------------------------------------------------------------------------
-- Grants explícitos (cubre objetos ya creados; RLS sigue gobernando filas)
-- ---------------------------------------------------------------------------
grant all on all tables    in schema conciliacion to anon, authenticated, service_role;
grant all on all sequences in schema conciliacion to anon, authenticated, service_role;
grant all on all routines  in schema conciliacion to anon, authenticated, service_role;
