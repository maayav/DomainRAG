"use client";

import { useState } from "react";
import { Citation } from "@/lib/api";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";

export function CitationCard({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const relevance = Math.round(citation.score * 100);

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      className="w-full text-left rounded-xl border border-border/50 bg-secondary/30 hover:bg-secondary/50 transition-colors duration-150 cursor-pointer"
    >
      <div className="flex items-center justify-between px-3 py-2.5">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex items-center justify-center w-5 h-5 rounded-md bg-teal-500/10 text-teal-400 shrink-0">
            <FileText size={11} />
          </div>
          <span className="text-xs font-medium text-foreground/80 truncate">
            {citation.source}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground/60 shrink-0">
            [{index}]
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <RelevancePill value={relevance} />
          {expanded ? (
            <ChevronUp size={12} className="text-muted-foreground" />
          ) : (
            <ChevronDown size={12} className="text-muted-foreground" />
          )}
        </div>
      </div>
      {expanded && (
        <div className="px-3 pb-3 pt-0">
          <div className="border-t border-border/30 pt-2.5">
            <p className="text-xs text-muted-foreground leading-relaxed">
              {citation.text}
            </p>
          </div>
        </div>
      )}
    </button>
  );
}

function RelevancePill({ value }: { value: number }) {
  let color = "text-red-400 bg-red-500/10";
  if (value >= 70) color = "text-emerald-400 bg-emerald-500/10";
  else if (value >= 50) color = "text-amber-400 bg-amber-500/10";

  return (
    <span
      className={`text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md ${color}`}
    >
      {value}%
    </span>
  );
}