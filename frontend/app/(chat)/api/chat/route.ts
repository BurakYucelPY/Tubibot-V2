import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  generateId,
} from "ai";
import { auth } from "@/app/(auth)/auth";
import {
  deleteChatById,
  getChatById,
  saveChat,
  saveMessages,
} from "@/lib/db/queries";
import { generateUUID } from "@/lib/utils";

export const maxDuration = 60;

const PYTHON_BACKEND_URL =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

const TITLE_MAX = 60;

function buildTitle(text: string): string {
  const trimmed = text.trim().replace(/\s+/g, " ");
  if (trimmed.length <= TITLE_MAX) {
    return trimmed;
  }
  return `${trimmed.slice(0, TITLE_MAX)}…`;
}

type IncomingMessage = {
  id?: string;
  parts?: { type: string; text?: string }[];
};

export async function POST(request: Request) {
  let body: Record<string, unknown>;

  try {
    body = await request.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const chatId = typeof body.id === "string" ? body.id : null;
  const incoming = body.message as IncomingMessage | undefined;

  let userText = "";
  if (incoming?.parts) {
    userText = incoming.parts
      .filter((p) => p.type === "text" && p.text)
      .map((p) => p.text)
      .join("");
  }

  if (!userText.trim()) {
    return new Response("Empty message", { status: 400 });
  }

  if (!chatId) {
    return new Response("Missing chat id", { status: 400 });
  }

  const session = await auth();
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }
  const userId = session.user.id;

  const selectedChatModel =
    typeof body.selectedChatModel === "string"
      ? body.selectedChatModel
      : "groq/llama-3.3-70b";

  const existing = await getChatById({ id: chatId });
  if (!existing) {
    await saveChat({
      id: chatId,
      userId,
      title: buildTitle(userText),
      visibility: "private",
    });
  } else if (existing.userId !== userId) {
    return new Response("Forbidden", { status: 403 });
  }

  const userMessageId = incoming?.id ?? generateUUID();
  await saveMessages({
    messages: [
      {
        id: userMessageId,
        chatId,
        role: "user",
        parts: incoming?.parts ?? [{ type: "text", text: userText }],
        attachments: [],
        createdAt: new Date(),
      },
    ],
  });

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const partId = generateId();
      const assistantId = generateUUID();
      let accumulated = "";

      const response = await fetch(`${PYTHON_BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, model: selectedChatModel }),
      });

      if (!response.ok || !response.body) {
        const errorId = generateId();
        writer.write({ type: "text-start", id: errorId });
        writer.write({
          type: "text-delta",
          id: errorId,
          delta:
            "Backend ile bağlantı kurulamadı. Lütfen Python backend'in çalıştığından emin olun.",
        });
        writer.write({ type: "text-end", id: errorId });
        return;
      }

      writer.write({ type: "text-start", id: partId });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        const text = decoder.decode(value, { stream: true });
        if (text) {
          accumulated += text;
          writer.write({ type: "text-delta", id: partId, delta: text });
        }
      }

      writer.write({ type: "text-end", id: partId });

      if (accumulated) {
        await saveMessages({
          messages: [
            {
              id: assistantId,
              chatId,
              role: "assistant",
              parts: [{ type: "text", text: accumulated }],
              attachments: [],
              createdAt: new Date(),
            },
          ],
        });
      }
    },
    generateId: generateUUID,
  });

  return createUIMessageStreamResponse({ stream });
}

export async function DELETE(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) {
    return new Response("Missing id", { status: 400 });
  }

  const chat = await getChatById({ id });
  if (!chat) {
    return Response.json({ success: true }, { status: 200 });
  }
  if (chat.userId !== session.user.id) {
    return new Response("Forbidden", { status: 403 });
  }

  const deleted = await deleteChatById({ id });
  return Response.json({ success: true, deleted }, { status: 200 });
}
