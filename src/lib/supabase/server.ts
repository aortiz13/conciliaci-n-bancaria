import { cookies } from "next/headers";

import { createServerClient, type CookieOptions } from "@supabase/ssr";

import { DB_SCHEMA } from "@/lib/supabase/constants";
import type { Database } from "@/lib/supabase/types";

type CookieToSet = { name: string; value: string; options?: CookieOptions };

/**
 * Cliente Supabase para Server Components, Route Handlers y Server Actions.
 * Usa la anon key + la sesión del usuario en cookies; sujeto a RLS por tenant.
 */
export function createClient() {
  const cookieStore = cookies();

  return createServerClient<Database, typeof DB_SCHEMA>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      db: { schema: DB_SCHEMA },
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet: CookieToSet[]) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // `setAll` se llama desde un Server Component: se puede ignorar
            // si hay middleware refrescando la sesión.
          }
        },
      },
    },
  );
}
