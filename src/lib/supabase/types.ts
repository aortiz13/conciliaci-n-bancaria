/**
 * Tipos de la base de datos Supabase.
 *
 * PLACEHOLDER: se regenera automáticamente a partir del schema con:
 *   supabase gen types typescript --project-id <ref> --schema public > src/lib/supabase/types.ts
 *
 * o vía MCP (`generate_typescript_types`) una vez aplicadas las migraciones.
 * Hasta entonces se usa un tipo laxo para no bloquear el build.
 */
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

// Tipo laxo temporal: se sustituye por el schema generado tras las migraciones.
type AnyDatabase = Record<string, never>;
export type Database = AnyDatabase & Record<string, unknown>;
