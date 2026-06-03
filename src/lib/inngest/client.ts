import { Inngest } from "inngest";

/**
 * Cliente Inngest. Orquesta la extracción asíncrona con reintentos durables
 * (PRD §10): aísla los fallos del LLM de la recepción del documento.
 */
export const inngest = new Inngest({ id: "conciliacion-bancaria" });

/** Eventos del sistema. */
export type DocumentReceivedEvent = {
  name: "invoice/document.received";
  data: {
    tenantId: string;
    documentId: string;
    storagePath: string;
    mime: string;
    channel: "telegram" | "email";
    /** Datos para responder al proveedor por su canal (opcional). */
    reply?: {
      telegramChatId?: number;
    };
  };
};
