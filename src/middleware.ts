import { type NextRequest } from "next/server";

import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Aplica a todas las rutas salvo:
     * - _next/static, _next/image (assets)
     * - favicon y archivos estáticos comunes
     * - rutas de webhooks de ingesta (no llevan sesión de usuario)
     */
    "/((?!_next/static|_next/image|favicon.ico|api/ingest|api/inngest|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
