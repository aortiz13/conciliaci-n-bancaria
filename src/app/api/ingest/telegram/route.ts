import { webhookCallback } from "grammy";

import { getBot } from "@/lib/telegram/bot";

// Procesamiento del documento en background; la recepción solo encola.
export const maxDuration = 60;

/**
 * Webhook de Telegram (RF-1). Valida el secret token configurado en
 * `setWebhook` y delega en el bot grammY.
 */
export async function POST(req: Request): Promise<Response> {
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (secret) {
    const header = req.headers.get("x-telegram-bot-api-secret-token");
    if (header !== secret) {
      return new Response("Unauthorized", { status: 401 });
    }
  }

  const handler = webhookCallback(getBot(), "std/http");
  return handler(req);
}
