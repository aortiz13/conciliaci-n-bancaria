-- 0001_extensions.sql
-- Extensiones necesarias para el MVP.

-- gen_random_uuid() para PKs uuid (incluido en Postgres >=13, vía pgcrypto).
create extension if not exists pgcrypto with schema extensions;

-- Matching de concepto por similitud (conciliación fuzzy) sin servicios externos.
create extension if not exists pg_trgm with schema extensions;
