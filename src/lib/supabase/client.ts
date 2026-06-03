import { createBrowserClient } from "@supabase/ssr";

import type { Database } from "@/lib/supabase/types";

/**
 * Cliente Supabase para componentes de cliente (navegador).
 * Usa la anon key y queda sujeto a las políticas RLS por tenant.
 */
export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
