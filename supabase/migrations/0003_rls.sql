-- 0003_rls.sql
-- Row Level Security por membresía de tenant (sección 9 del PRD).
-- Las funciones helper son SECURITY DEFINER para evitar recursión de RLS
-- al consultar `memberships` desde las propias políticas.

-- ---------------------------------------------------------------------------
-- Helpers de autorización
-- ---------------------------------------------------------------------------
create or replace function public.is_tenant_member(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = auth.uid()
  );
$$;

create or replace function public.is_tenant_admin(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = auth.uid()
      and m.role = 'admin'
  );
$$;

-- ---------------------------------------------------------------------------
-- Habilitar RLS en todas las tablas
-- ---------------------------------------------------------------------------
alter table public.plans                 enable row level security;
alter table public.tenants               enable row level security;
alter table public.users                 enable row level security;
alter table public.memberships           enable row level security;
alter table public.suppliers             enable row level security;
alter table public.channel_identities    enable row level security;
alter table public.documents             enable row level security;
alter table public.invoices              enable row level security;
alter table public.invoice_lines         enable row level security;
alter table public.invoice_tax_subtotals enable row level security;
alter table public.bank_statements       enable row level security;
alter table public.bank_movements        enable row level security;
alter table public.reconciliation_matches enable row level security;
alter table public.match_links           enable row level security;
alter table public.exceptions_queue      enable row level security;
alter table public.conversations         enable row level security;
alter table public.messages              enable row level security;
alter table public.usage_counters        enable row level security;
alter table public.audit_log             enable row level security;
alter table public.erp_connections       enable row level security;

-- ---------------------------------------------------------------------------
-- plans: catálogo de solo lectura para usuarios autenticados
-- ---------------------------------------------------------------------------
create policy plans_select on public.plans
  for select to authenticated using (true);

-- ---------------------------------------------------------------------------
-- tenants: miembros leen; admin actualiza
-- ---------------------------------------------------------------------------
create policy tenants_select on public.tenants
  for select to authenticated using (public.is_tenant_member(id));
create policy tenants_update on public.tenants
  for update to authenticated
  using (public.is_tenant_admin(id))
  with check (public.is_tenant_admin(id));

-- ---------------------------------------------------------------------------
-- users: cada usuario gestiona su propia fila
-- ---------------------------------------------------------------------------
create policy users_select on public.users
  for select to authenticated using (id = auth.uid());
create policy users_insert on public.users
  for insert to authenticated with check (id = auth.uid());
create policy users_update on public.users
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---------------------------------------------------------------------------
-- memberships: miembros del tenant leen; admin gestiona
-- ---------------------------------------------------------------------------
create policy memberships_select on public.memberships
  for select to authenticated using (public.is_tenant_member(tenant_id));
create policy memberships_admin_write on public.memberships
  for all to authenticated
  using (public.is_tenant_admin(tenant_id))
  with check (public.is_tenant_admin(tenant_id));

-- ---------------------------------------------------------------------------
-- Tablas operativas: CRUD completo para cualquier miembro (admin u operador)
-- ---------------------------------------------------------------------------
-- Patrón: USING + WITH CHECK sobre is_tenant_member(tenant_id).
create policy suppliers_rw on public.suppliers
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy channel_identities_rw on public.channel_identities
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy documents_rw on public.documents
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy invoices_rw on public.invoices
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy invoice_lines_rw on public.invoice_lines
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy invoice_tax_subtotals_rw on public.invoice_tax_subtotals
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy bank_statements_rw on public.bank_statements
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy bank_movements_rw on public.bank_movements
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy reconciliation_matches_rw on public.reconciliation_matches
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy match_links_rw on public.match_links
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy exceptions_queue_rw on public.exceptions_queue
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy conversations_rw on public.conversations
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

create policy messages_rw on public.messages
  for all to authenticated
  using (public.is_tenant_member(tenant_id))
  with check (public.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- usage_counters: miembros leen; escritura solo backend (service_role)
-- ---------------------------------------------------------------------------
create policy usage_counters_select on public.usage_counters
  for select to authenticated using (public.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- audit_log: miembros leen e insertan (append-only); sin update/delete
-- ---------------------------------------------------------------------------
create policy audit_log_select on public.audit_log
  for select to authenticated using (public.is_tenant_member(tenant_id));
create policy audit_log_insert on public.audit_log
  for insert to authenticated with check (public.is_tenant_member(tenant_id));

-- ---------------------------------------------------------------------------
-- erp_connections: solo admin (contiene credenciales)
-- ---------------------------------------------------------------------------
create policy erp_connections_admin on public.erp_connections
  for all to authenticated
  using (public.is_tenant_admin(tenant_id))
  with check (public.is_tenant_admin(tenant_id));
