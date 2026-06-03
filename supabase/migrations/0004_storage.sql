-- 0004_storage.sql
-- Storage privado para archivos originales de factura.
-- Patrón: un bucket privado `invoices`; el primer segmento del path es el
-- `tenant_id`, y las políticas RLS sobre storage.objects exigen membresía.
-- Ej. de path:  <tenant_id>/<document_id>.<ext>

insert into storage.buckets (id, name, public)
values ('invoices', 'invoices', false)
on conflict (id) do nothing;

-- Lectura: miembros del tenant dueño de la carpeta.
create policy "invoices_select_members"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'invoices'
    and public.is_tenant_member(((storage.foldername(name))[1])::uuid)
  );

-- Escritura/actualización/borrado: miembros del tenant dueño de la carpeta.
create policy "invoices_insert_members"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'invoices'
    and public.is_tenant_member(((storage.foldername(name))[1])::uuid)
  );

create policy "invoices_update_members"
  on storage.objects for update to authenticated
  using (
    bucket_id = 'invoices'
    and public.is_tenant_member(((storage.foldername(name))[1])::uuid)
  )
  with check (
    bucket_id = 'invoices'
    and public.is_tenant_member(((storage.foldername(name))[1])::uuid)
  );

create policy "invoices_delete_members"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'invoices'
    and public.is_tenant_member(((storage.foldername(name))[1])::uuid)
  );
