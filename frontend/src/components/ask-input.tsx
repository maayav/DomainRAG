"use client";

import { useEffect, useRef } from "react";
import { ArrowUp, Globe, Loader2, Plus } from "lucide-react";
import Magnet from "@/components/bits/magnet";

interface AskInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
  uploading?: boolean;
  onUpload: () => void;
  onScrape: () => void;
  placeholder?: string;
  autoFocus?: boolean;
  focusSignal?: number;
  className?: string;
}

export function AskInput({
  value,
  onChange,
  onSubmit,
  loading,
  uploading = false,
  onUpload,
  onScrape,
  placeholder = "Ask a question...",
  autoFocus = false,
  focusSignal = 0,
  className = "",
}: AskInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus) textareaRef.current?.focus();
  }, [autoFocus, focusSignal]);

  const autoResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + "px";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !loading) {
      e.preventDefault();
      onSubmit();
    }
  };

  const canSend = value.trim().length > 0 && !loading;

  return (
    <div
      className={`relative flex flex-col rounded-2xl border border-border bg-card shadow-[0_8px_32px_rgba(0,0,0,0.25)] transition-all duration-200 focus-within:border-ring/60 focus-within:shadow-[0_0_0_3px_color-mix(in_oklab,var(--ring)_16%,transparent),0_8px_32px_rgba(0,0,0,0.25)] ${className}`}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={autoResize}
        onKeyDown={handleKeyDown}
        rows={1}
        aria-label="Ask the knowledge base"
        disabled={loading}
        placeholder={placeholder}
        className="w-full resize-none bg-transparent px-4 py-4 text-[15px] leading-relaxed text-foreground outline-none placeholder:text-muted-foreground/50 disabled:opacity-60 max-h-45 min-h-[56px]"
      />

      <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onUpload}
            disabled={uploading || loading}
            title="Add documents to the knowledge base"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:opacity-40"
          >
            {uploading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Plus size={16} />
            )}
          </button>
          <button
            type="button"
            onClick={onScrape}
            disabled={loading}
            title="Scrape a web page into the knowledge base"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground disabled:opacity-40"
          >
            <Globe size={16} />
          </button>
        </div>

        <Magnet
          padding={10}
          magnetStrength={3}
          disabled={!canSend}
          innerClassName={!canSend ? "cursor-not-allowed" : ""}
        >
          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSend}
            aria-label="Send question"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm transition-colors hover:brightness-110 disabled:opacity-40 disabled:shadow-none"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ArrowUp size={16} strokeWidth={2.2} />
            )}
          </button>
        </Magnet>
      </div>
    </div>
  );
}