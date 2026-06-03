-- 0006_increment_usage.sql
-- Incremento atómico del contador de documentos por tenant y periodo (RF-26).
-- Se invoca como RPC desde el servicio de extracción (service_role).

create or replace function conciliacion.increment_usage(
  p_tenant_id uuid,
  p_periodo text
)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into conciliacion.usage_counters (tenant_id, periodo, docs_count)
  values (p_tenant_id, p_periodo, 1)
  on conflict (tenant_id, periodo)
  do update set docs_count = conciliacion.usage_counters.docs_count + 1,
                updated_at = now();
$$;

grant execute on function conciliacion.increment_usage(uuid, text)
  to service_role, authenticated;
