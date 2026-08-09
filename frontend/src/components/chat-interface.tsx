"use client";

import { useEffect, useRef, useState } from "react";
import {
  Check,
  AlertCircle,
  RotateCcw,
  Settings,
} from "lucide-react";
import { AskInput } from "./ask-input";
import { WelcomeStage } from "./welcome-stage";
import { SourceStrip } from "./source-strip";
import { NotesPanel } from "./notes-panel";
import { SettingsModal } from "./settings-modal";
import { ScrapeModal } from "./scrape-modal";
import {
  streamQuery,
  uploadDocuments,
  healthCheck,
  Citation,
} from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

interface UploadNotice {
  type: "success" | "error";
  text: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadNotice, setUploadNotice] = useState<UploadNotice | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [scrapeOpen, setScrapeOpen] = useState(false);
  const [currentModel, setCurrentModel] = useState("local");
  const [docCount, setDocCount] = useState<number | null>(null);
  const [online, setOnline] = useState(false);
  const [openSources, setOpenSources] = useState<Record<string, boolean>>({});
  const [view, setView] = useState<"ask" | "notes">("ask");

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    healthCheck()
      .then((res) => {
        if (!cancelled) {
          setOnline(true);
          setDocCount(res.documents);
        }
      })
      .catch(() => {
        if (!cancelled) setOnline(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSubmit = async (query?: string) => {
    const text = query || input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg: Message = { id: assistantMsgId, role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);
    setOpenSources((prev) => ({ ...prev, [assistantMsgId]: true }));

    const updateMessage = (fn: (m: Message) => Message) =>
      setMessages((prev) => prev.map((m) => (m.id === assistantMsgId ? fn(m) : m)));

    try {
      await streamQuery(text, {
        onThinking: () => {},
        onCitations: (citations) => {
          updateMessage((m) => ({ ...m, citations }));
        },
        onToken: (token) => {
          updateMessage((m) => ({ ...m, content: m.content + token }));
        },
        onDone: () => {},
        onError: (detail) => {
          updateMessage((m) => ({
            ...m,
            content: m.content || detail || "Answer generation failed",
          }));
        },
      });
    } catch {
      updateMessage((m) => ({
        ...m,
        content:
          m.content ||
          "Unable to reach the backend. Make sure the server is running on port 8000.",
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0 || uploading) return;
    setUploading(true);
    setUploadNotice(null);
    try {
      const res = await uploadDocuments(Array.from(files));
      const parts = [
        `Added ${res.uploaded.length} document${res.uploaded.length === 1 ? "" : "s"}`,
        ...res.uploaded,
      ];
      if (res.skipped.length > 0) {
        parts.push(
          `Skipped ${res.skipped.length}: ${res.skipped.map((s) => s.name).join(", ")}`
        );
      }
      setUploadNotice({ type: "success", text: parts.join(" — ") });
      healthCheck()
        .then((r) => setDocCount(r.documents))
        .catch(() => {});
    } catch (e) {
      setUploadNotice({
        type: "error",
        text: e instanceof Error ? e.message : "Upload failed",
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const resetConversation = () => {
    setMessages([]);
    setInput("");
    setOpenSources({});
  };

  const showWelcome = messages.length === 0;

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      {/* ── Ribbon ── */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-5 md:px-8">
        <div className="flex items-center gap-4">
          <div className="font-mono text-[15px] font-bold tracking-tight">
            domain<span className="text-muted-foreground">/</span>rag
          </div>
          <div className="hidden items-center gap-2 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground md:flex">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                online ? "bg-emerald-500" : "bg-destructive"
              }`}
            />
            <span>{online ? "local" : "offline"}</span>
            {online && docCount !== null && (
              <>
                <span className="text-border">·</span>
                <span>{docCount} chunks</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg border border-border bg-secondary/60 p-0.5">
            {(["ask", "notes"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setView(v)}
                className={`rounded-md px-3 py-1 font-mono text-[11px] tracking-wide transition-colors ${
                  view === v
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {v === "ask" ? "Ask" : "Notes"}
              </button>
            ))}
          </div>
          <span className="hidden font-mono text-[11px] text-muted-foreground sm:inline">
            {currentModel}
          </span>
          <button
            type="button"
            onClick={resetConversation}
            title="Start a new conversation"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <RotateCcw size={15} />
          </button>
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            title="Model settings"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <Settings size={16} />
          </button>
        </div>
      </header>

      {/* ── Conversation ── */}
      <main className="relative flex min-h-0 flex-1 flex-col">
        {view === "notes" ? (
          <NotesPanel />
        ) : (
          <>     
        <div ref={scrollRef} className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-4 md:px-8">
          <div className="mx-auto w-full max-w-3xl">
            {showWelcome ? (
              <WelcomeStage
                docCount={docCount}
                online={online}
                onSubmit={handleSubmit}
              />
            ) : (
              <div className="space-y-8 pb-40 pt-8">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex w-full animate-message-in ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <div className="max-w-[80%] rounded-2xl border border-border bg-secondary/70 px-4 py-2.5 text-[15px] leading-relaxed text-secondary-foreground">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="w-full max-w-[92%]">
                        {msg.content ? (
                          <p className="text-[15px] leading-[1.75] whitespace-pre-wrap">
                            {msg.content}
                            {msg.citations && msg.citations.length > 0 && (
                              <sup
                                className="cite-mark"
                                onClick={() =>
                                  setOpenSources((prev) => ({
                                    ...prev,
                                    [msg.id]: !prev[msg.id],
                                  }))
                                }
                                role="button"
                                aria-label="Toggle sources"
                              >
                                {msg.citations.map((_, i) => `[${i + 1}]`).join(" ")}
                              </sup>
                            )}
                          </p>
                        ) : (
                          <div className="flex items-center gap-1.5 py-3">
                            <span
                              className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-pulse-dot"
                              style={{ animationDelay: "0ms" }}
                            />
                            <span
                              className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-pulse-dot"
                              style={{ animationDelay: "200ms" }}
                            />
                            <span
                              className="h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-pulse-dot"
                              style={{ animationDelay: "400ms" }}
                            />
                          </div>
                        )}
                        {msg.citations && msg.citations.length > 0 && (
                          <SourceStrip
                            citations={msg.citations}
                            open={!!openSources[msg.id]}
                            onToggle={() =>
                              setOpenSources((prev) => ({
                                ...prev,
                                [msg.id]: !prev[msg.id],
                              }))
                            }
                          />
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Composer ── */}
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background/95 to-transparent px-4 pb-4 pt-14 md:px-8">
          <div className="pointer-events-auto mx-auto w-full max-w-3xl">
            {uploadNotice && (
              <div
                className={`mb-2 flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs ${
                  uploadNotice.type === "success"
                    ? "bg-emerald-500/10 text-emerald-600"
                    : "bg-destructive/10 text-destructive"
                }`}
              >
                {uploadNotice.type === "success" ? (
                  <Check size={13} />
                ) : (
                  <AlertCircle size={13} />
                )}
                <span className="break-all">{uploadNotice.text}</span>
              </div>
            )}
            <AskInput
              value={input}
              onChange={setInput}
              onSubmit={() => handleSubmit()}
              loading={loading}
              uploading={uploading}
              onUpload={() => fileInputRef.current?.click()}
              onScrape={() => setScrapeOpen(true)}
              placeholder="Ask the technical wiki..."
              autoFocus
              focusSignal={messages.length}
            />
            <p className="mt-2.5 text-center font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground/50">
              Local-first — nothing leaves this machine
            </p>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".md,.txt,.rst,.pdf,.html,.htm,.csv,.json,.yaml,.yml,.docx,.pptx,.xlsx"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        </>
        )}
      </main>

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={(label) => setCurrentModel(label)}
      />
      <ScrapeModal
        open={scrapeOpen}
        onClose={() => setScrapeOpen(false)}
      />
    </div>
  );
}