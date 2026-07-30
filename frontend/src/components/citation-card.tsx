"use client";

import { Citation } from "@/lib/api";

export function CitationCard({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  return (
    <div className="w-full text-left rounded-xl border border-border bg-background p-4 shadow-sm">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-[11px] font-mono font-medium text-muted-foreground bg-secondary px-1.5 py-0.5 rounded-sm">
          [{index}]
        </span>
        <a
          href={citation.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-foreground truncate hover:text-primary hover:underline transition-colors"
        >
          {citation.source}
        </a>
      </div>
      
      <div className="mb-3">
        <p className="text-[13px] text-muted-foreground leading-relaxed line-clamp-4">
          ...{citation.text.trim().startsWith("...") ? citation.text.substring(3) : citation.text}...
        </p>
      </div>

      <div className="flex items-center justify-between mt-auto">
        <span className="text-[11px] text-muted-foreground/60">
          Similarity: {(citation.score).toFixed(2)}
        </span>
      </div>
    </div>
  );
}