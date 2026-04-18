import "server-only";

import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

export type StoredChat = {
  id: string;
  createdAt: string;
  title: string;
  userId: string;
  kind?: "default" | "gundem";
};

export type StoredMessage = {
  id: string;
  chatId: string;
  role: string;
  parts: unknown;
  attachments: unknown;
  createdAt: string;
};

type StoreShape = {
  chats: StoredChat[];
  messages: StoredMessage[];
};

const DATA_DIR = join(process.cwd(), ".local-data");
const DATA_FILE = join(DATA_DIR, "tubibot.json");

const EMPTY_STORE: StoreShape = { chats: [], messages: [] };

let cache: StoreShape | null = null;
let writeQueue: Promise<void> = Promise.resolve();

async function readFromDisk(): Promise<StoreShape> {
  try {
    const raw = await readFile(DATA_FILE, "utf8");
    const parsed = JSON.parse(raw) as Partial<StoreShape>;
    return {
      chats: Array.isArray(parsed.chats) ? parsed.chats : [],
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
    };
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return { chats: [], messages: [] };
    }
    throw err;
  }
}

export async function loadStore(): Promise<StoreShape> {
  if (cache) {
    return cache;
  }
  cache = await readFromDisk();
  return cache;
}

async function writeToDisk(data: StoreShape): Promise<void> {
  await mkdir(dirname(DATA_FILE), { recursive: true });
  const tmp = `${DATA_FILE}.${randomUUID()}.tmp`;
  await writeFile(tmp, JSON.stringify(data, null, 2), "utf8");
  await rename(tmp, DATA_FILE);
}

export async function saveStore(data: StoreShape): Promise<void> {
  cache = data;
  const snapshot: StoreShape = {
    chats: [...data.chats],
    messages: [...data.messages],
  };
  writeQueue = writeQueue.then(() => writeToDisk(snapshot)).catch((err) => {
    console.error("[local-store] write failed", err);
  });
  await writeQueue;
}

export async function mutateStore<T>(
  fn: (store: StoreShape) => { store: StoreShape; result: T }
): Promise<T> {
  const current = await loadStore();
  const { store: next, result } = fn({
    chats: [...current.chats],
    messages: [...current.messages],
  });
  await saveStore(next);
  return result;
}

export function chatToDomain(row: StoredChat) {
  return {
    id: row.id,
    createdAt: new Date(row.createdAt),
    title: row.title,
    userId: row.userId,
    kind: row.kind ?? "default",
  };
}

export function messageToDomain(row: StoredMessage) {
  return {
    id: row.id,
    chatId: row.chatId,
    role: row.role,
    parts: row.parts,
    attachments: row.attachments,
    createdAt: new Date(row.createdAt),
  };
}

export const __TEST__ = { EMPTY_STORE, DATA_FILE };
