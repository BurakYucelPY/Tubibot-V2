import "server-only";

import type { ArtifactKind } from "@/components/chat/artifact";
import type { VisibilityType } from "@/components/chat/visibility-selector";
import type {
  Chat,
  DBMessage,
  Document,
  Suggestion,
  User,
  Vote,
} from "./schema";

// Mock DB — no PostgreSQL needed. All functions return empty/mock data.

export async function getUser(_email: string): Promise<User[]> {
  return [];
}

export async function createUser(_email: string, _password: string) {
  return;
}

export async function createGuestUser() {
  return [{ id: "guest-user-id", email: "guest@tubibot.local" }];
}

export async function saveChat(_args: {
  id: string;
  userId: string;
  title: string;
  visibility: VisibilityType;
}) {
  return;
}

export async function deleteChatById(_args: { id: string }): Promise<Chat | undefined> {
  return undefined;
}

export async function deleteAllChatsByUserId(_args: { userId: string }) {
  return { deletedCount: 0 };
}

export async function getChatsByUserId(_args: {
  id: string;
  limit: number;
  startingAfter: string | null;
  endingBefore: string | null;
}): Promise<{ chats: Chat[]; hasMore: boolean }> {
  return { chats: [], hasMore: false };
}

export async function getChatById(_args: { id: string }): Promise<Chat | null> {
  return null;
}

export async function saveMessages(_args: { messages: DBMessage[] }) {
  return;
}

export async function updateMessage(_args: {
  id: string;
  parts: DBMessage["parts"];
}) {
  return;
}

export async function getMessagesByChatId(_args: { id: string }): Promise<DBMessage[]> {
  return [];
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

export async function getDocumentsById(_args: { id: string }): Promise<Document[]> {
  return [];
}

export async function getDocumentById(_args: { id: string }): Promise<Document | undefined> {
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

export async function getMessageById(_args: { id: string }): Promise<DBMessage[]> {
  return [];
}

export async function deleteMessagesByChatIdAfterTimestamp(_args: {
  chatId: string;
  timestamp: Date;
}) {
  return;
}

export async function updateChatVisibilityById(_args: {
  chatId: string;
  visibility: "private" | "public";
}) {
  return;
}

export async function updateChatTitleById(_args: {
  chatId: string;
  title: string;
}) {
  return;
}

export async function getMessageCountByUserId(_args: {
  id: string;
  differenceInHours: number;
}): Promise<number> {
  return 0;
}

export async function createStreamId(_args: {
  streamId: string;
  chatId: string;
}) {
  return;
}

export async function getStreamIdsByChatId(_args: { chatId: string }): Promise<string[]> {
  return [];
}
