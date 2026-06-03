import type { AppSupabaseClient } from "@/lib/supabase/admin";

/**
 * Resuelve el tenant a partir del alias de email inbound (RF-2).
 * El alias completo es `<email_alias>@<INBOUND_EMAIL_DOMAIN>`; aquí se busca
 * por la parte local (`email_alias`).
 */
export async function resolveTenantByEmailAlias(
  admin: AppSupabaseClient,
  recipient: string,
): Promise<string | null> {
  const alias = recipient.split("@")[0]?.trim().toLowerCase();
  if (!alias) return null;

  const { data, error } = await admin
    .from("tenants")
    .select("id")
    .eq("email_alias", alias)
    .maybeSingle();
  if (error) throw new Error(`Tenant lookup failed: ${error.message}`);
  return (data?.id as string) ?? null;
}

/**
 * Resuelve el tenant para un mensaje de Telegram.
 *
 * MVP: si la identidad de canal ya existe (`channel_identities`), se usa su
 * tenant. Si no, se recurre a `DEFAULT_TENANT_ID` (despliegue de bot por
 * tenant). El soporte multi-tenant sobre un único bot queda como mejora.
 */
export async function resolveTenantForTelegram(
  admin: AppSupabaseClient,
  telegramValue: string,
): Promise<string | null> {
  const { data, error } = await admin
    .from("channel_identities")
    .select("tenant_id")
    .eq("tipo", "telegram")
    .eq("valor", telegramValue)
    .maybeSingle();
  if (error) throw new Error(`Channel lookup failed: ${error.message}`);
  if (data?.tenant_id) return data.tenant_id as string;

  return process.env.DEFAULT_TENANT_ID ?? null;
}
