import { createBrowserClient } from "@supabase/ssr";

import { DB_SCHEMA } from "@/lib/supabase/constants";
import type { Database } from "@/lib/supabase/types";

/**
 * Cliente Supabase para componentes de cliente (navegador).
 * Usa la anon key y queda sujeto a las políticas RLS por tenant.
 * Apunta por defecto al esquema dedicado `conciliacion`.
 */
export function createClient() {
  return createBrowserClient<Database, typeof DB_SCHEMA>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { db: { schema: DB_SCHEMA } },
  );
}
