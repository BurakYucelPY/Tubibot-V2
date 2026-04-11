import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  generateId,
} from "ai";
import { generateUUID } from "@/lib/utils";

export const maxDuration = 60;

const PYTHON_BACKEND_URL =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

export async function POST(request: Request) {
  let body: Record<string, unknown>;

  try {
    body = await request.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  // Extract user message text from the AI SDK message format
  const message = body.message as
    | { parts?: { type: string; text?: string }[] }
    | undefined;

  let userText = "";
  if (message?.parts) {
    userText = message.parts
      .filter((p) => p.type === "text" && p.text)
      .map((p) => p.text)
      .join("");
  }

  if (!userText.trim()) {
    return new Response("Empty message", { status: 400 });
  }

  const selectedChatModel =
    typeof body.selectedChatModel === "string"
      ? body.selectedChatModel
      : "groq/llama-3.3-70b";

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const partId = generateId();

      // Call our Python FastAPI backend
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

      // Start text part
      writer.write({ type: "text-start", id: partId });

      // Stream the response from FastAPI
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        if (text) {
          writer.write({ type: "text-delta", id: partId, delta: text });
        }
      }

      // Finish text part
      writer.write({ type: "text-end", id: partId });
    },
    generateId: generateUUID,
  });

  return createUIMessageStreamResponse({ stream });
}

export async function DELETE() {
  return Response.json({ success: true }, { status: 200 });
}
