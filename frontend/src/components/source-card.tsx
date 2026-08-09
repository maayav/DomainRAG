"use client";

import { Citation } from "@/lib/api";

export function SourceCard({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  const host = (() => {
    try {
      return new URL(citation.url).hostname;
    } catch {
      return citation.source;
    }
  })();

  return (
    <div className="group rounded-lg border border-border bg-card/40 px-4 py-3 transition-colors hover:border-ring/40">
      <div className="flex items-baseline justify-between gap-3">
        <span className="shrink-0 font-mono text-[11px] font-medium text-accent">
          [{String(index).padStart(2, "0")}]
        </span>
        <a
          href={citation.url}
          target="_blank"
          rel="noopener noreferrer"
          title={citation.url}
          className="min-w-0 flex-1 truncate text-left text-[13px] font-medium text-foreground transition-colors hover:text-accent"
        >
          {citation.source}
        </a>
        <span className="shrink-0 font-mono text-[10px] text-muted-foreground/70">
          {Math.round(citation.score * 100)}%
        </span>
      </div>

      <a
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-0.5 block truncate pl-7 font-mono text-[11px] text-muted-foreground/70 transition-colors hover:text-muted-foreground"
      >
        {host || citation.url}
      </a>

      <p className="mt-2 pl-7 text-[13px] leading-relaxed text-muted-foreground">
        <span className="line-clamp-3">
          {citation.text.trim().startsWith("...")
            ? citation.text.trim().slice(3)
            : citation.text.trim()}
        </span>
      </p>
    </div>
  );
}