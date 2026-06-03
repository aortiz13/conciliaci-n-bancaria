-- 0001_extensions.sql
-- Extensiones + esquema dedicado `conciliacion` (aislado de otras apps del
-- proyecto, que viven en `public`).

-- gen_random_uuid() para PKs uuid (incluido en Postgres >=13, vía pgcrypto).
create extension if not exists pgcrypto with schema extensions;

-- Matching de concepto por similitud (conciliación fuzzy) sin servicios externos.
create extension if not exists pg_trgm with schema extensions;

-- Esquema propio del producto.
create schema if not exists conciliacion;

-- Acceso de los roles de Supabase al esquema (RLS sigue gobernando filas).
grant usage on schema conciliacion to anon, authenticated, service_role;

-- Privilegios por defecto para objetos que se creen a continuación.
alter default privileges in schema conciliacion
  grant all on tables to anon, authenticated, service_role;
alter default privileges in schema conciliacion
  grant all on sequences to anon, authenticated, service_role;
alter default privileges in schema conciliacion
  grant all on functions to anon, authenticated, service_role;
