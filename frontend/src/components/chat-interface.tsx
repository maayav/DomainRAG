"use client";

import { useState, useRef, useEffect } from "react";
import { CitationCard } from "./citation-card";
import { queryQuestion, Citation, healthCheck } from "@/lib/api";
import {
  ArrowUp,
  Loader2,
  Sparkles,
  BookOpen,
  Zap,
  Code,
  Database,
  Shield,
} from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

const SUGGESTIONS = [
  { icon: Code, text: "What are Python decorators?" },
  { icon: Database, text: "How does Docker networking work?" },
  { icon: Shield, text: "Explain SQL injection prevention" },
  { icon: Zap, text: "What is async/await in Python?" },
];

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [docCount, setDocCount] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    healthCheck()
      .then((data) => {
        setConnected(true);
        setDocCount(data.documents);
      })
      .catch(() => setConnected(false));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSubmit = async (query?: string) => {
    const text = query || input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }

    try {
      const res = await queryQuestion(text);
      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        citations: res.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Unable to reach the backend. Make sure the server is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
      // Re-focus input after response
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const autoResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  };

  const isEmptyState = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-emerald-600">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight">DomainRAG</h1>
            <p className="text-[11px] text-muted-foreground leading-none">
              Technical Knowledge Assistant
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-secondary/50 px-2.5 py-1 rounded-full">
            <BookOpen size={12} />
            <span>{docCount} docs</span>
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full ${
              connected
                ? "text-emerald-400 bg-emerald-500/10"
                : "text-red-400 bg-red-500/10"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                connected ? "bg-emerald-400" : "bg-red-400"
              }`}
            />
            {connected ? "Online" : "Offline"}
          </div>
        </div>
      </header>

      {/* ── Messages area ── */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto custom-scrollbar"
      >
        {isEmptyState ? (
          /* ── Empty state ── */
          <div className="flex flex-col items-center justify-center h-full px-4 animate-fade-in">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500/20 to-emerald-600/20 border border-teal-500/20 mb-6">
              <Sparkles size={24} className="text-teal-400" />
            </div>
            <h2 className="text-xl font-semibold mb-1">
              What would you like to know?
            </h2>
            <p className="text-sm text-muted-foreground mb-8 max-w-md text-center">
              Ask questions about Python, SQL, Docker, Git, REST APIs, Linux,
              and more from the knowledge base.
            </p>
            <div className="grid grid-cols-2 gap-2.5 w-full max-w-lg">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSubmit(s.text)}
                  className="flex items-center gap-2.5 px-4 py-3 rounded-xl border border-border/60 bg-card/50 hover:bg-card hover:border-border text-sm text-left transition-all duration-200 group cursor-pointer"
                >
                  <s.icon
                    size={15}
                    className="text-muted-foreground group-hover:text-teal-400 transition-colors shrink-0"
                  />
                  <span className="text-muted-foreground group-hover:text-foreground transition-colors">
                    {s.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* ── Message thread ── */
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg, i) => (
              <div
                key={i}
                className="animate-message-in"
                style={{ animationDelay: `${(i % 4) * 50}ms` }}
              >
                {msg.role === "user" ? (
                  /* User message */
                  <div className="flex justify-end">
                    <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-br-md bg-secondary text-sm leading-relaxed">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  /* Assistant message */
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-5 h-5 rounded-md bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center">
                        <Sparkles size={11} className="text-white" />
                      </div>
                      <span className="text-xs font-medium text-muted-foreground">
                        DomainRAG
                      </span>
                    </div>
                    <div className="text-sm leading-relaxed text-foreground/90 pl-7">
                      {msg.content}
                    </div>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pl-7 mt-4">
                        <div className="flex items-center gap-1.5 mb-2.5">
                          <BookOpen
                            size={12}
                            className="text-muted-foreground"
                          />
                          <span className="text-xs font-medium text-muted-foreground">
                            Sources
                          </span>
                        </div>
                        <div className="space-y-2">
                          {msg.citations.map((c, j) => (
                            <CitationCard
                              key={j}
                              citation={c}
                              index={j + 1}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="animate-message-in">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-5 h-5 rounded-md bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center">
                    <Sparkles size={11} className="text-white" />
                  </div>
                  <span className="text-xs font-medium text-muted-foreground">
                    DomainRAG
                  </span>
                </div>
                <div className="pl-7 flex items-center gap-1.5 py-2">
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse-dot"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse-dot"
                    style={{ animationDelay: "200ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse-dot"
                    style={{ animationDelay: "400ms" }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Input area ── */}
      <div className="px-4 pb-4 pt-2">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-end gap-2 rounded-2xl border border-border/60 bg-card/80 backdrop-blur-sm px-4 py-3 focus-within:border-teal-500/40 focus-within:ring-1 focus-within:ring-teal-500/20 transition-all duration-200">
            <textarea
              ref={inputRef}
              value={input}
              onChange={autoResize}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              disabled={loading}
              rows={1}
              className="flex-1 bg-transparent text-sm resize-none outline-none placeholder:text-muted-foreground/60 max-h-40 disabled:opacity-50"
            />
            <button
              onClick={() => handleSubmit()}
              disabled={loading || !input.trim()}
              className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center bg-foreground text-background disabled:opacity-30 hover:opacity-90 transition-opacity cursor-pointer disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <ArrowUp size={14} strokeWidth={2.5} />
              )}
            </button>
          </div>
          <p className="text-[11px] text-muted-foreground/50 text-center mt-2">
            Powered by Llama 3.2 · LlamaIndex · FAISS
          </p>
        </div>
      </div>
    </div>
  );
}
