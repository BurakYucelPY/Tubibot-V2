"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useActiveChat } from "@/hooks/use-active-chat";
import type { Attachment, ChatMessage } from "@/lib/types";
import { StarField } from "@/components/landing/StarField";
import { ChatHeader } from "./chat-header";
import { submitEditedMessage } from "./message-editor";
import { Messages } from "./messages";
import { MultimodalInput } from "./multimodal-input";

/** Anasayfanın kırmızı radial glow + yıldız efektini chat'e taşıyan arka plan katmanı */
function ChatBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      {/* Ana kırmızı glow — sol üstten yayılan, anasayfayla aynı renk paleti */}
      <svg
        className="absolute -top-20 -left-10 h-[140%] w-[90%]"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="chat-glow-main" cx="12%" cy="20%">
            <stop offset="0%" stopColor="rgba(248, 56, 56, 0.13)" />
            <stop offset="35%" stopColor="rgba(180, 0, 0, 0.05)" />
            <stop offset="65%" stopColor="rgba(100, 0, 0, 0.01)" />
            <stop offset="100%" stopColor="rgba(10, 14, 23, 0)" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#chat-glow-main)" />
      </svg>

      {/* Alt kırmızı accent — sol alt */}
      <svg
        className="absolute -bottom-10 -left-5 h-[50%] w-[50%]"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="chat-glow-bottom" cx="0%" cy="100%">
            <stop offset="0%" stopColor="rgba(180, 0, 0, 0.15)" />
            <stop offset="100%" stopColor="rgba(10, 14, 23, 0)" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#chat-glow-bottom)" />
      </svg>

      {/* Yıldız alanı — anasayfadan alınan StarField bileşeni, orta kısımda görünür */}
      <StarField className="top-[50%] left-[5%] opacity-50" />
    </div>
  );
}


export function ChatShell() {
  const {
    chatId,
    messages,
    setMessages,
    sendMessage,
    status,
    stop,
    regenerate,
    addToolApprovalResponse,
    input,
    setInput,
    visibilityType,
    isReadonly,
    isLoading,
    votes,
    currentModelId,
    setCurrentModelId,
    showCreditCardAlert,
    setShowCreditCardAlert,
  } = useActiveChat();

  const pathname = usePathname();
  const isBlankView =
    pathname === "/haberler-duyurular" || pathname === "/dokumanlar";

  const [editingMessage, setEditingMessage] = useState<ChatMessage | null>(
    null
  );
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const stopRef = useRef(stop);
  stopRef.current = stop;

  const prevChatIdRef = useRef(chatId);
  useEffect(() => {
    if (prevChatIdRef.current !== chatId) {
      prevChatIdRef.current = chatId;
      stopRef.current();
      setEditingMessage(null);
      setAttachments([]);
    }
  }, [chatId]);

  return (
    <>
      <div className="flex h-dvh w-full flex-row overflow-hidden">
        <div className="flex w-full min-w-0 flex-col bg-sidebar">
          <ChatHeader
            chatId={chatId}
            isReadonly={isReadonly}
            selectedVisibilityType={visibilityType}
          />

          <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-background md:rounded-tl-[12px] md:border-t md:border-l md:border-border/40">
            {/* Anasayfa temalı arka plan katmanı */}
            <ChatBackground />

            {!isBlankView && (
              <>
                <Messages
                  addToolApprovalResponse={addToolApprovalResponse}
                  chatId={chatId}
                  isLoading={isLoading}
                  isReadonly={isReadonly}
                  messages={messages}
                  onEditMessage={(msg) => {
                    const text = msg.parts
                      ?.filter((p) => p.type === "text")
                      .map((p) => p.text)
                      .join("");
                    setInput(text ?? "");
                    setEditingMessage(msg);
                  }}
                  regenerate={regenerate}
                  selectedModelId={currentModelId}
                  setMessages={setMessages}
                  status={status}
                  votes={votes}
                />

                <div className="sticky bottom-0 z-1 mx-auto flex w-full max-w-4xl gap-2 border-t-0 bg-transparent px-2 pb-3 md:px-4 md:pb-4">
                  {!isReadonly && (
                    <MultimodalInput
                      attachments={attachments}
                      chatId={chatId}
                      editingMessage={editingMessage}
                      input={input}
                      isLoading={isLoading}
                      messages={messages}
                      onCancelEdit={() => {
                        setEditingMessage(null);
                        setInput("");
                      }}
                      onModelChange={setCurrentModelId}
                      selectedModelId={currentModelId}
                      selectedVisibilityType={visibilityType}
                      sendMessage={
                        editingMessage
                          ? async () => {
                            const msg = editingMessage;
                            setEditingMessage(null);
                            await submitEditedMessage({
                              message: msg,
                              text: input,
                              setMessages,
                              regenerate,
                            });
                            setInput("");
                          }
                          : sendMessage
                      }
                      setAttachments={setAttachments}
                      setInput={setInput}
                      setMessages={setMessages}
                      status={status}
                      stop={stop}
                    />
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <AlertDialog
        onOpenChange={setShowCreditCardAlert}
        open={showCreditCardAlert}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Activate AI Gateway</AlertDialogTitle>
            <AlertDialogDescription>
              This application requires{" "}
              {process.env.NODE_ENV === "production" ? "the owner" : "you"} to
              activate Vercel AI Gateway.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                window.open(
                  "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card",
                  "_blank"
                );
                window.location.href = `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/`;
              }}
            >
              Activate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
