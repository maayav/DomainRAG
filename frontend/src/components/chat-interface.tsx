"use client";

import { useState, useRef, useEffect } from "react";
import { CitationCard } from "./citation-card";
import { SettingsModal } from "./settings-modal";
import { streamQuery, uploadDocuments, Citation } from "@/lib/api";
import {
  ArrowUp,
  Loader2,
  X,
  Globe,
  Plus,
  Settings,
  Check,
  AlertCircle
} from "lucide-react";

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
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadNotice, setUploadNotice] = useState<UploadNotice | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentModel, setCurrentModel] = useState("local");

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // Focus input when messages change (if not loading)
  useEffect(() => {
    if (messages.length > 0 && !loading) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [messages.length, loading]);

  const handleSubmit = async (query?: string) => {
    const text = query || input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg: Message = { id: assistantMsgId, role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    const updateMessage = (fn: (m: Message) => Message) =>
      setMessages((prev) => prev.map((m) => (m.id === assistantMsgId ? fn(m) : m)));

    try {
      await streamQuery(text, {
        onThinking: () => {
          /* thinking steps are shown via the typing indicator */
        },
        onCitations: (citations) => {
          updateMessage((m) => ({ ...m, citations }));
          setActiveMessageId(assistantMsgId);
        },
        onToken: (token) => {
          updateMessage((m) => ({ ...m, content: m.content + token }));
        },
        onDone: () => {
          /* content already streamed */
        },
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

  const activeMessage = messages.find(m => m.id === activeMessageId);
  const showSidebar = activeMessageId !== null && activeMessage?.citations && activeMessage.citations.length > 0;

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0 || uploading) return;
    setUploading(true);
    setUploadNotice(null);
    try {
      const res = await uploadDocuments(Array.from(files));
      const parts = [`Added ${res.uploaded.length} document${res.uploaded.length === 1 ? "" : "s"}`, ...res.uploaded];
      if (res.skipped.length > 0) {
        parts.push(`Skipped ${res.skipped.length}: ${res.skipped.map((s) => s.name).join(", ")}`);
      }
      setUploadNotice({ type: "success", text: parts.join(" — ") });
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

  return (
    <div className="flex flex-col h-full bg-background text-foreground font-sans">
      {/* ── Top Header ── */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-background z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="text-xl tracking-tight flex items-center">
            <span className="font-semibold text-foreground">Domain</span>
            <span className="font-light text-foreground">RAG</span>
          </div>
          <div className="hidden md:flex items-center gap-3 ml-2">
            <span className="text-sm text-muted-foreground">Domain-specific RAG assistant with evaluated retrieval</span>
            <span className="text-[10px] font-semibold tracking-wider uppercase bg-secondary text-secondary-foreground px-2 py-1 rounded-sm">
              Mixed Tech Wiki
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-muted-foreground/70 hidden sm:inline">{currentModel}</span>
          <button
            onClick={() => setSettingsOpen(true)}
            title="Model settings"
            className="p-2 rounded-md hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          >
            <Settings size={18} />
          </button>
        </div>
      </header>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Column: Chat Area */}
        <div className="flex-1 flex flex-col relative min-w-0">
          
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-8 py-6 custom-scrollbar">
            <div className="max-w-4xl mx-auto space-y-8 pb-32">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full min-h-[40vh]">
                  <p className="text-muted-foreground text-sm">Ask a technical question to get started...</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`flex w-full animate-message-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    
                    {msg.role === "user" ? (
                      <div className="max-w-[80%] bg-secondary/60 text-secondary-foreground px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="max-w-[90%] md:max-w-[85%]">
                        <div 
                          className="text-[15px] leading-relaxed text-foreground cursor-text whitespace-pre-wrap"
                          onClick={() => {
                            if (msg.citations && msg.citations.length > 0) {
                              setActiveMessageId(msg.id);
                            }
                          }}
                        >
                          {msg.content}
                        </div>
                        {/* Optional subtle indicator that citations exist if sidebar is closed */}
                        {msg.citations && msg.citations.length > 0 && activeMessageId !== msg.id && (
                          <button 
                            onClick={() => setActiveMessageId(msg.id)}
                            className="mt-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                          >
                            <Globe size={12} /> View {msg.citations.length} Citations
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}

              {/* Typing indicator */}
              {loading && (
                <div className="flex justify-start w-full animate-message-in">
                  <div className="flex items-center gap-1.5 py-4 px-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-pulse-dot" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-pulse-dot" style={{ animationDelay: "200ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-pulse-dot" style={{ animationDelay: "400ms" }} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Box Area */}
          <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background to-transparent pointer-events-none">
            <div className="max-w-4xl mx-auto pointer-events-auto">
              {/* Input Container */}
              <div className="relative flex flex-col rounded-2xl border border-border bg-background shadow-lg overflow-hidden focus-within:border-muted-foreground/50 transition-colors">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={autoResize}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a technical question..."
                  disabled={loading}
                  rows={1}
                  className="w-full bg-transparent text-[15px] resize-none outline-none placeholder:text-muted-foreground/60 max-h-40 disabled:opacity-50 px-4 py-4 min-h-[80px]"
                />
                
                {/* Input Toolbar */}
                <div className="flex items-center justify-between px-3 pb-3">
                  <div className="flex items-center gap-1">
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".md,.txt,.rst,.pdf"
                      className="hidden"
                      onChange={(e) => handleFiles(e.target.files)}
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      title="Add documents to the knowledge base"
                      className="p-2 rounded-md hover:bg-secondary text-muted-foreground transition-colors disabled:opacity-40"
                    >
                      {uploading ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <Plus size={18} />
                      )}
                    </button>
                  </div>
                  <button
                    onClick={() => handleSubmit()}
                    disabled={loading || !input.trim()}
                    className="w-8 h-8 rounded-md flex items-center justify-center bg-secondary hover:bg-secondary-foreground hover:text-background text-foreground disabled:opacity-30 transition-all cursor-pointer disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <ArrowUp size={16} strokeWidth={2} />
                    )}
                  </button>
                </div>
              </div>
              {uploadNotice && (
                <div className={`mt-2 flex items-center gap-1.5 text-xs px-3 py-2 rounded-md ${
                  uploadNotice.type === "success"
                    ? "bg-emerald-500/10 text-emerald-600"
                    : "bg-destructive/10 text-destructive"
                }`}>
                  {uploadNotice.type === "success" ? <Check size={13} /> : <AlertCircle size={13} />}
                  <span className="break-all">{uploadNotice.text}</span>
                </div>
              )}
              <div className="text-center mt-3">
                <span className="text-[11px] text-muted-foreground/50">
                  DomainRAG can make mistakes. Check important info.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Context Explorer Sidebar */}
        {showSidebar && (
          <div className="w-[350px] shrink-0 border-l border-border bg-background flex flex-col animate-fade-in z-20">
            {/* Sidebar Header */}
            <div className="flex items-center justify-between px-5 py-4">
              <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">Context Explorer</h2>
              <button 
                onClick={() => setActiveMessageId(null)}
                className="p-1 rounded-md hover:bg-secondary text-muted-foreground transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            
            {/* Tabs */}
            <div className="flex items-center border-b border-border px-4">
              <span className="px-4 py-2.5 text-sm font-medium border-b-2 border-foreground text-foreground">
                Citations
              </span>
            </div>

            {/* Sidebar Content (Citations) */}
            <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4 custom-scrollbar bg-secondary/10">
              {activeMessage?.citations?.map((c, i) => (
                <CitationCard key={i} citation={c} index={i + 1} />
              ))}
            </div>
          </div>
        )}
      </div>

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={(label) => setCurrentModel(label)}
      />
    </div>
  );
}
