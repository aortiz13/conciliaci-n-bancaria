import { createClient as createSupabaseClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/types";

/**
 * Cliente Supabase con `service_role`. SALTA RLS.
 *
 * USO EXCLUSIVO en backend/serverless de confianza (webhook ingest, jobs de
 * Inngest, servicio de extracción). NUNCA importar desde código de cliente.
 * El filtrado por `tenant_id` es responsabilidad del llamante (defense-in-depth).
 */
export function createAdminClient() {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    throw new Error("SUPABASE_SERVICE_ROLE_KEY no está configurada");
  }

  return createSupabaseClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    serviceRoleKey,
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    },
  );
}
