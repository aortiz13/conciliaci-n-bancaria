import { persistDocument } from "@/lib/ingest/documents";
import { resolveTenantByEmailAlias } from "@/lib/ingest/tenant";
import { inngest } from "@/lib/inngest/client";
import { createAdminClient } from "@/lib/supabase/admin";

export const maxDuration = 60;

const ACCEPTED_MIME = new Set([
  "application/pdf",
  "image/jpeg",
  "image/jpg",
  "image/png",
]);

/** Extrae la primera dirección de email de un campo "Nombre <a@b>". */
function parseAddress(raw: string | null): string | null {
  if (!raw) return null;
  const match = raw.match(/[^<\s]+@[^>\s]+/);
  return match ? match[0] : null;
}

/**
 * Webhook de SendGrid Inbound Parse (RF-2). Recibe el correo como
 * multipart/form-data; resuelve el tenant por el alias destinatario y encola
 * cada adjunto de factura.
 */
export async function POST(req: Request): Promise<Response> {
  const secret = process.env.SENDGRID_INBOUND_SECRET;
  if (secret) {
    const url = new URL(req.url);
    if (url.searchParams.get("secret") !== secret) {
      return new Response("Unauthorized", { status: 401 });
    }
  }

  const form = await req.formData();
  const recipient = parseAddress(form.get("to") as string | null);
  if (!recipient) {
    return new Response("Missing recipient", { status: 400 });
  }

  const admin = createAdminClient();
  const tenantId = await resolveTenantByEmailAlias(admin, recipient);
  if (!tenantId) {
    // 200 para que SendGrid no reintente un alias inexistente.
    return Response.json({ ignored: "unknown alias" });
  }

  let encolados = 0;
  for (const [, value] of form.entries()) {
    if (!(value instanceof File)) continue;
    const mime = value.type || "application/octet-stream";
    if (!ACCEPTED_MIME.has(mime)) continue;

    const fileBytes = new Uint8Array(await value.arrayBuffer());
    const { documentId, storagePath } = await persistDocument(admin, {
      tenantId,
      fileBytes,
      mime,
      channel: "email",
    });

    await inngest.send({
      name: "invoice/document.received",
      data: { tenantId, documentId, storagePath, mime, channel: "email" },
    });
    encolados += 1;
  }

  return Response.json({ tenantId, encolados });
}
