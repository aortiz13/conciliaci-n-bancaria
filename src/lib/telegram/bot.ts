import { Bot, type Context } from "grammy";

import { persistDocument } from "@/lib/ingest/documents";
import { resolveTenantForTelegram } from "@/lib/ingest/tenant";
import { inngest } from "@/lib/inngest/client";
import { createAdminClient } from "@/lib/supabase/admin";

// Aviso obligatorio de IA (EU AI Act Art. 50 — RF-9).
const AI_DISCLAIMER =
  "🤖 Soy un asistente automático (IA). Envíame tu factura en PDF o foto y la registro al instante.";

const MAX_BYTES = 20 * 1024 * 1024; // Límite de Telegram Bot API.

let _bot: Bot | null = null;

/** Bot grammY singleton (token desde `TELEGRAM_BOT_TOKEN`). */
export function getBot(): Bot {
  if (_bot) return _bot;

  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) throw new Error("TELEGRAM_BOT_TOKEN no está configurada");

  const bot = new Bot(token);

  bot.command("start", (ctx) => ctx.reply(AI_DISCLAIMER));

  bot.on(["message:document", "message:photo"], async (ctx) => {
    await handleIncomingFile(ctx, token);
  });

  // Cualquier otro mensaje: guía + declaración de IA.
  bot.on("message", (ctx) => ctx.reply(AI_DISCLAIMER));

  _bot = bot;
  return bot;
}

async function handleIncomingFile(ctx: Context, token: string): Promise<void> {
  const from = ctx.from;
  const chatId = ctx.chat?.id;
  if (!from || chatId === undefined) return;

  const telegramValue = from.username ? `@${from.username}` : `id:${from.id}`;

  let mime = "application/octet-stream";
  if (ctx.message?.document) {
    mime = ctx.message.document.mime_type ?? "application/octet-stream";
  } else if (ctx.message?.photo) {
    mime = "image/jpeg";
  }

  const admin = createAdminClient();
  const tenantId = await resolveTenantForTelegram(admin, telegramValue);
  if (!tenantId) {
    await ctx.reply(
      "No encuentro la empresa asociada a este chat. Contacta con quien te invitó.",
    );
    return;
  }

  let file;
  try {
    file = await ctx.getFile(); // falla si supera el límite de Telegram
  } catch {
    await ctx.reply(
      `El archivo supera el límite de ${MAX_BYTES / 1024 / 1024} MB de Telegram. ` +
        "Envíalo por email a tu alias o comprime el PDF.",
    );
    return;
  }

  const fileUrl = `https://api.telegram.org/file/bot${token}/${file.file_path}`;
  const res = await fetch(fileUrl);
  const fileBytes = new Uint8Array(await res.arrayBuffer());

  const { documentId, storagePath } = await persistDocument(admin, {
    tenantId,
    fileBytes,
    mime,
    channel: "telegram",
  });

  await inngest.send({
    name: "invoice/document.received",
    data: {
      tenantId,
      documentId,
      storagePath,
      mime,
      channel: "telegram",
      reply: { telegramChatId: chatId },
    },
  });

  await ctx.reply(
    "✅ Factura recibida y en proceso. Te aviso si falta algún dato. " +
      AI_DISCLAIMER,
  );
}
