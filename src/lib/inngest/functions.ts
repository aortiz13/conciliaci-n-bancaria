import { inngest, type DocumentReceivedEvent } from "@/lib/inngest/client";

/**
 * URL del servicio de extracción Python (Vercel serverless). Por defecto,
 * relativo al propio despliegue (`/api/extract`).
 */
function extractionUrl(): string {
  const base = process.env.EXTRACTION_SERVICE_URL;
  if (base) return base;
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  return `${appUrl}/api/extract`;
}

type ExtractionResult = {
  estado: string;
  invoice_id: string | null;
  duplicate_of: string | null;
  validations: string[];
  supplier_id: string | null;
  error?: string;
};

/**
 * Procesa un documento recibido: llama al servicio de extracción Python.
 * Inngest reintenta de forma idempotente ante fallos transitorios del LLM.
 */
export const extractInvoice = inngest.createFunction(
  {
    id: "extract-invoice",
    retries: 4,
    triggers: [{ event: "invoice/document.received" }],
  },
  async ({ event, step }) => {
    const { tenantId, documentId, storagePath, mime } =
      event.data as DocumentReceivedEvent["data"];

    const result = await step.run("call-extraction-service", async () => {
      const res = await fetch(extractionUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: tenantId,
          document_id: documentId,
          storage_path: storagePath,
          mime,
        }),
      });
      const json = (await res.json()) as ExtractionResult;
      if (!res.ok) {
        // Lanzar para que Inngest reintente.
        throw new Error(json.error ?? `Extraction failed (${res.status})`);
      }
      return json;
    });

    return result;
  },
);

export const functions = [extractInvoice];
