import "server-only";

import type { VisibilityType } from "@/components/chat/visibility-selector";
import {
  chatToDomain,
  loadStore,
  messageToDomain,
  mutateStore,
  type StoredChat,
  type StoredMessage,
} from "./local-store";
import type {
  Chat,
  DBMessage,
  Document,
  Suggestion,
  User,
  Vote,
} from "./schema";

type ArtifactKind = "text" | "code" | "image" | "sheet";

// --- File-backed (real) implementations ---

export async function saveChat(args: {
  id: string;
  userId: string;
  title: string;
  visibility: VisibilityType;
}) {
  await mutateStore((store) => {
    const existingIdx = store.chats.findIndex((c) => c.id === args.id);
    const row: StoredChat = {
      id: args.id,
      userId: args.userId,
      title: args.title,
      visibility: args.visibility,
      createdAt:
        existingIdx >= 0
          ? store.chats[existingIdx].createdAt
          : new Date().toISOString(),
    };
    if (existingIdx >= 0) {
      store.chats[existingIdx] = row;
    } else {
      store.chats.push(row);
    }
    return { store, result: undefined };
  });
}

export async function getChatById(args: { id: string }): Promise<Chat | null> {
  const store = await loadStore();
  const row = store.chats.find((c) => c.id === args.id);
  return row ? (chatToDomain(row) as Chat) : null;
}

export async function getChatsByUserId(args: {
  id: string;
  limit: number;
  startingAfter: string | null;
  endingBefore: string | null;
}): Promise<{ chats: Chat[]; hasMore: boolean }> {
  const store = await loadStore();
  const sorted = store.chats
    .filter((c) => c.userId === args.id)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  let startIdx = 0;
  if (args.endingBefore) {
    const idx = sorted.findIndex((c) => c.id === args.endingBefore);
    if (idx >= 0) {
      startIdx = idx + 1;
    }
  } else if (args.startingAfter) {
    const idx = sorted.findIndex((c) => c.id === args.startingAfter);
    if (idx >= 0) {
      startIdx = idx + 1;
    }
  }

  const slice = sorted.slice(startIdx, startIdx + args.limit);
  const hasMore = sorted.length > startIdx + args.limit;

  return {
    chats: slice.map((c) => chatToDomain(c) as Chat),
    hasMore,
  };
}

export async function deleteChatById(args: {
  id: string;
}): Promise<Chat | undefined> {
  return await mutateStore((store) => {
    const idx = store.chats.findIndex((c) => c.id === args.id);
    if (idx < 0) {
      return { store, result: undefined };
    }
    const removed = store.chats[idx];
    store.chats.splice(idx, 1);
    store.messages = store.messages.filter((m) => m.chatId !== args.id);
    return { store, result: chatToDomain(removed) as Chat };
  });
}

export async function deleteAllChatsByUserId(args: { userId: string }) {
  return await mutateStore((store) => {
    const toDelete = new Set(
      store.chats.filter((c) => c.userId === args.userId).map((c) => c.id)
    );
    store.chats = store.chats.filter((c) => !toDelete.has(c.id));
    store.messages = store.messages.filter((m) => !toDelete.has(m.chatId));
    return { store, result: { deletedCount: toDelete.size } };
  });
}

export async function saveMessages(args: { messages: DBMessage[] }) {
  await mutateStore((store) => {
    for (const msg of args.messages) {
      const row: StoredMessage = {
        id: msg.id,
        chatId: msg.chatId,
        role: msg.role,
        parts: msg.parts,
        attachments: msg.attachments,
        createdAt:
          msg.createdAt instanceof Date
            ? msg.createdAt.toISOString()
            : new Date(msg.createdAt as unknown as string).toISOString(),
      };
      const idx = store.messages.findIndex((m) => m.id === msg.id);
      if (idx >= 0) {
        store.messages[idx] = row;
      } else {
        store.messages.push(row);
      }
    }
    return { store, result: undefined };
  });
}

export async function updateMessage(args: {
  id: string;
  parts: DBMessage["parts"];
}) {
  await mutateStore((store) => {
    const idx = store.messages.findIndex((m) => m.id === args.id);
    if (idx >= 0) {
      store.messages[idx] = { ...store.messages[idx], parts: args.parts };
    }
    return { store, result: undefined };
  });
}

export async function getMessagesByChatId(args: {
  id: string;
}): Promise<DBMessage[]> {
  const store = await loadStore();
  return store.messages
    .filter((m) => m.chatId === args.id)
    .sort((a, b) => a.createdAt.localeCompare(b.createdAt))
    .map((m) => messageToDomain(m) as DBMessage);
}

export async function getMessageById(args: {
  id: string;
}): Promise<DBMessage[]> {
  const store = await loadStore();
  const row = store.messages.find((m) => m.id === args.id);
  return row ? [messageToDomain(row) as DBMessage] : [];
}

export async function deleteMessagesByChatIdAfterTimestamp(args: {
  chatId: string;
  timestamp: Date;
}) {
  const cutoff = args.timestamp.toISOString();
  await mutateStore((store) => {
    store.messages = store.messages.filter(
      (m) => !(m.chatId === args.chatId && m.createdAt >= cutoff)
    );
    return { store, result: undefined };
  });
}

export async function updateChatVisibilityById(args: {
  chatId: string;
  visibility: "private" | "public";
}) {
  await mutateStore((store) => {
    const idx = store.chats.findIndex((c) => c.id === args.chatId);
    if (idx >= 0) {
      store.chats[idx] = { ...store.chats[idx], visibility: args.visibility };
    }
    return { store, result: undefined };
  });
}

export async function updateChatTitleById(args: {
  chatId: string;
  title: string;
}) {
  await mutateStore((store) => {
    const idx = store.chats.findIndex((c) => c.id === args.chatId);
    if (idx >= 0) {
      store.chats[idx] = { ...store.chats[idx], title: args.title };
    }
    return { store, result: undefined };
  });
}

export async function getMessageCountByUserId(args: {
  id: string;
  differenceInHours: number;
}): Promise<number> {
  const store = await loadStore();
  const cutoff = new Date(
    Date.now() - args.differenceInHours * 60 * 60 * 1000
  ).toISOString();
  const userChatIds = new Set(
    store.chats.filter((c) => c.userId === args.id).map((c) => c.id)
  );
  return store.messages.filter(
    (m) => userChatIds.has(m.chatId) && m.createdAt >= cutoff
  ).length;
}

// --- Still mocked (intentionally) ---

export async function getUser(_email: string): Promise<User[]> {
  return [];
}

export async function createUser(_email: string, _password: string) {
  return;
}

export async function createGuestUser() {
  return [{ id: "guest-user-id", email: "guest@tubibot.local" }];
}

export async function voteMessage(_args: {
  chatId: string;
  messageId: string;
  type: "up" | "down";
}) {
  return;
}

export async function getVotesByChatId(_args: { id: string }): Promise<Vote[]> {
  return [];
}

export async function saveDocument(_args: {
  id: string;
  title: string;
  kind: ArtifactKind;
  content: string;
  userId: string;
}): Promise<Document[]> {
  return [];
}

export async function updateDocumentContent(_args: {
  id: string;
  content: string;
}): Promise<Document[]> {
  return [];
}

export async function getDocumentsById(_args: {
  id: string;
}): Promise<Document[]> {
  return [];
}

export async function getDocumentById(_args: {
  id: string;
}): Promise<Document | undefined> {
  return undefined;
}

export async function deleteDocumentsByIdAfterTimestamp(_args: {
  id: string;
  timestamp: Date;
}): Promise<Document[]> {
  return [];
}

export async function saveSuggestions(_args: { suggestions: Suggestion[] }) {
  return;
}

export async function getSuggestionsByDocumentId(_args: {
  documentId: string;
}): Promise<Suggestion[]> {
  return [];
}

export async function createStreamId(_args: {
  streamId: string;
  chatId: string;
}) {
  return;
}

export async function getStreamIdsByChatId(_args: {
  chatId: string;
}): Promise<string[]> {
  return [];
}
