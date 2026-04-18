"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { motion } from "framer-motion";
import { ArrowUpIcon } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { unstable_serialize } from "swr/infinite";
import { Suggestion } from "@/components/ai-elements/suggestion";
import {
  PromptInput,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { DEFAULT_CHAT_MODEL } from "@/lib/ai/models";
import type { ChatMessage } from "@/lib/types";
import { cn, fetcher, fetchWithErrorHandlers, generateUUID } from "@/lib/utils";
import { getChatHistoryPaginationKey } from "./sidebar-history";
import { Messages } from "./messages";
import { ModelSelectorCompact } from "./multimodal-input";

const GUNDEM_SUGGESTIONS = [
  "TÜBİTAK'ın bu hafta açıklanan yeni çağrıları neler?",
  "Son duyurulan ikili iş birliği programları hangileri?",
  "TEYDEB destek programlarıyla ilgili güncel haberler neler?",
  "TEKNOFEST yarışmalarına dair son gelişmeler neler?",
];

function GundemGreeting() {
  return (
    <div className="flex flex-col items-center px-4" key="gundem-overview">
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="text-center font-semibold text-2xl tracking-tight text-foreground md:text-3xl"
        initial={{ opacity: 0, y: 10 }}
        transition={{ delay: 0.35, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        Bugün TÜBİTAK gündeminde ne var?
      </motion.div>
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="mt-3 text-center text-muted-foreground/80 text-sm"
        initial={{ opacity: 0, y: 10 }}
        transition={{ delay: 0.5, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        TÜBİTAK&apos;ın son duyuruları, açık çağrıları ve haberleri hakkında
        soru sorun.
      </motion.div>
    </div>
  );
}

function GundemSuggestions({
  onSelect,
}: {
  onSelect: (question: string) => void | Promise<void>;
}) {
  return (
    <div
      className="flex w-full gap-2.5 overflow-x-auto pb-1 sm:grid sm:grid-cols-2 sm:overflow-visible"
      style={{
        scrollbarWidth: "none",
        WebkitOverflowScrolling: "touch",
        msOverflowStyle: "none",
      }}
    >
      {GUNDEM_SUGGESTIONS.map((question, index) => (
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="min-w-[200px] shrink-0 sm:min-w-0 sm:shrink"
          exit={{ opacity: 0, y: 16 }}
          initial={{ opacity: 0, y: 16 }}
          key={question}
          transition={{
            delay: 0.06 * index,
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          <Suggestion
            className="h-auto w-full whitespace-nowrap rounded-xl border border-border/50 bg-card/30 px-4 py-3 text-left text-[12px] leading-relaxed text-muted-foreground transition-all duration-200 sm:whitespace-normal sm:p-4 sm:text-[13px] hover:-translate-y-0.5 hover:bg-card/60 hover:text-foreground hover:shadow-[var(--shadow-card)]"
            onClick={onSelect}
            suggestion={question}
          >
            {question}
          </Suggestion>
        </motion.div>
      ))}
    </div>
  );
}

export function GundemSorView() {
  const pathname = usePathname();
  const { mutate } = useSWRConfig();

  const urlChatId = pathname?.startsWith("/gundem-sor/")
    ? pathname.split("/")[2]
    : null;
  const isNewChat = !urlChatId;

  const newChatIdRef = useRef(generateUUID());
  const prevPathnameRef = useRef(pathname);
  if (isNewChat && prevPathnameRef.current !== pathname) {
    newChatIdRef.current = generateUUID();
  }
  prevPathnameRef.current = pathname;

  const chatId = urlChatId ?? newChatIdRef.current;

  const [input, setInput] = useState("");
  const [selectedModelId, setSelectedModelId] = useState(DEFAULT_CHAT_MODEL);
  const selectedModelIdRef = useRef(selectedModelId);
  selectedModelIdRef.current = selectedModelId;

  const { data: chatData } = useSWR(
    isNewChat
      ? null
      : `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/api/messages?chatId=${chatId}`,
    fetcher,
    { revalidateOnFocus: false }
  );

  const initialMessages: ChatMessage[] = isNewChat
    ? []
    : (chatData?.messages ?? []);

  const {
    messages,
    setMessages,
    sendMessage,
    status,
    regenerate,
    addToolApprovalResponse,
  } = useChat<ChatMessage>({
    id: chatId,
    messages: initialMessages,
    generateId: generateUUID,
    transport: new DefaultChatTransport({
      api: `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/api/chat-gundem`,
      fetch: fetchWithErrorHandlers,
      prepareSendMessagesRequest(request) {
        return {
          body: {
            id: request.id,
            message: request.messages.at(-1),
            selectedChatModel: selectedModelIdRef.current,
            ...request.body,
          },
        };
      },
    }),
    onFinish: () => {
      mutate(unstable_serialize(getChatHistoryPaginationKey));
    },
  });

  const loadedChatIds = useRef(new Set<string>());
  useEffect(() => {
    if (loadedChatIds.current.has(chatId)) {
      return;
    }
    if (chatData?.messages) {
      loadedChatIds.current.add(chatId);
      setMessages(chatData.messages);
    }
  }, [chatId, chatData?.messages, setMessages]);

  const prevChatIdRef = useRef(chatId);
  useEffect(() => {
    if (prevChatIdRef.current !== chatId) {
      prevChatIdRef.current = chatId;
      if (isNewChat) {
        setMessages([]);
      }
    }
  }, [chatId, isNewChat, setMessages]);

  const hasMessages = messages.length > 0;

  useEffect(() => {
    if (hasMessages) {
      return;
    }
    const timer = setTimeout(() => {
      const textarea = document.querySelector<HTMLTextAreaElement>(
        'textarea[name="message"]'
      );
      textarea?.focus();
    }, 100);
    return () => clearTimeout(timer);
  }, [hasMessages]);

  const handleSubmit = (message: { text: string }) => {
    const text = message.text.trim();
    if (!text) {
      return;
    }
    setInput("");
    sendMessage({
      role: "user",
      parts: [{ type: "text", text }],
    });
  };

  const isBusy = status === "submitted" || status === "streaming";

  return (
    <>
      {hasMessages ? (
        <Messages
          addToolApprovalResponse={addToolApprovalResponse}
          chatId={chatId}
          isLoading={false}
          isReadonly={false}
          messages={messages}
          regenerate={regenerate}
          selectedModelId={selectedModelId}
          setMessages={setMessages}
          status={status}
          votes={undefined}
        />
      ) : (
        <div className="relative z-1 flex flex-1 items-center justify-center px-4">
          <GundemGreeting />
        </div>
      )}

      <div className="sticky bottom-0 z-1 mx-auto flex w-full max-w-4xl flex-col gap-4 border-t-0 bg-transparent px-2 pb-3 md:px-4 md:pb-4">
        {!hasMessages && (
          <GundemSuggestions
            onSelect={(q) =>
              sendMessage({
                role: "user",
                parts: [{ type: "text", text: q }],
              })
            }
          />
        )}

        <PromptInput
          className="[&>div]:rounded-2xl [&>div]:border [&>div]:border-border/30 [&>div]:bg-card/70 [&>div]:shadow-[var(--shadow-composer)] [&>div]:transition-shadow [&>div]:duration-300 [&>div]:focus-within:shadow-[var(--shadow-composer-focus)]"
          onSubmit={handleSubmit}
        >
          <PromptInputTextarea
            autoFocus
            className="min-h-24 text-[13px] leading-relaxed px-4 pt-3.5 pb-1.5 placeholder:text-muted-foreground/35"
            onChange={(e) => setInput(e.currentTarget.value)}
            placeholder="Gündem hakkında bir şey sorun..."
            value={input}
          />
          <PromptInputFooter className="px-3 pb-3">
            <PromptInputTools>
              <ModelSelectorCompact
                onModelChange={setSelectedModelId}
                selectedModelId={selectedModelId}
              />
            </PromptInputTools>
            <PromptInputSubmit
              className={cn(
                "h-7 w-7 rounded-xl transition-all duration-200",
                input.trim() && !isBusy
                  ? "bg-foreground text-background hover:opacity-85 active:scale-95"
                  : "bg-muted text-muted-foreground/25 cursor-not-allowed"
              )}
              disabled={!input.trim() || isBusy}
              status={isBusy ? "submitted" : "ready"}
              variant="secondary"
            >
              <ArrowUpIcon className="size-4" />
            </PromptInputSubmit>
          </PromptInputFooter>
        </PromptInput>
      </div>
    </>
  );
}
