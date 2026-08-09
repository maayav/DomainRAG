"use client";

import { ChevronDown } from "lucide-react";
import { Citation } from "@/lib/api";
import { SourceCard } from "./source-card";

interface SourceStripProps {
  citations: Citation[];
  open: boolean;
  onToggle: () => void;
}

export function SourceStrip({ citations, open, onToggle }: SourceStripProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-4 border-t border-border/60 pt-3">
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-2 text-muted-foreground transition-colors hover:text-foreground"
        aria-expanded={open}
      >
        <span className="font-mono text-[10px] font-medium uppercase tracking-[0.22em]">
          Sources
        </span>
        <span className="rounded-full border border-border bg-secondary/60 px-2 py-px font-mono text-[10px] text-muted-foreground">
          {citations.length}
        </span>
        <ChevronDown
          size={13}
          className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      <div className={`sources-panel ${open ? "open" : ""}`}>
        <div>
          <div className="mt-3 space-y-2 pb-1">
            {citations.map((c, i) => (
              <SourceCard key={i} citation={c} index={i + 1} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}