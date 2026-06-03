/**
 * Esquema Postgres dedicado del producto. Aislado de otras apps que viven en
 * `public`. Debe estar expuesto en Supabase (Settings → API → Exposed schemas)
 * para que PostgREST/supabase-js lo sirva.
 */
export const DB_SCHEMA = "conciliacion" as const;
