import { NextResponse, type NextRequest } from "next/server";

import { createServerClient, type CookieOptions } from "@supabase/ssr";

import type { Database } from "@/lib/supabase/types";

type CookieToSet = { name: string; value: string; options?: CookieOptions };

/**
 * Refresca la sesión de Supabase en cada request y la propaga a las cookies.
 * Se invoca desde el middleware raíz.
 */
export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: CookieToSet[]) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // Refresca el token si ha expirado. No quitar: mantiene viva la sesión.
  await supabase.auth.getUser();

  return response;
}
