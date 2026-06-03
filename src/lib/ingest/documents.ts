import { createHash, randomUUID } from "crypto";

import type { AppSupabaseClient } from "@/lib/supabase/admin";

const BUCKET = "invoices";

export type PersistedDocument = {
  documentId: string;
  storagePath: string;
  hash: string;
};

/** Extensión a partir del mime (para nombrar el objeto en Storage). */
function extFor(mime: string): string {
  const map: Record<string, string> = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
  };
  return map[mime] ?? "bin";
}

/**
 * Sube el archivo original al bucket privado del tenant y registra el
 * documento. El path es `<tenant_id>/<uuid>.<ext>` (las políticas RLS de
 * Storage exigen membresía sobre la primera carpeta).
 *
 * Usa el cliente admin (service_role); el filtrado por tenant es explícito.
 */
export async function persistDocument(
  admin: AppSupabaseClient,
  params: {
    tenantId: string;
    fileBytes: Uint8Array;
    mime: string;
    channel: "telegram" | "email";
  },
): Promise<PersistedDocument> {
  const { tenantId, fileBytes, mime, channel } = params;

  const hash = createHash("sha256").update(fileBytes).digest("hex");
  const storagePath = `${tenantId}/${randomUUID()}.${extFor(mime)}`;

  const upload = await admin.storage
    .from(BUCKET)
    .upload(storagePath, fileBytes, { contentType: mime, upsert: false });
  if (upload.error) {
    throw new Error(`Storage upload failed: ${upload.error.message}`);
  }

  const { data, error } = await admin
    .from("documents")
    .insert({
      tenant_id: tenantId,
      storage_path: storagePath,
      mime,
      hash,
      origen_canal: channel,
    })
    .select("id")
    .single();
  if (error) {
    throw new Error(`Document insert failed: ${error.message}`);
  }

  return { documentId: data.id as string, storagePath, hash };
}
