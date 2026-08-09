"use client";

import SplitText from "@/components/bits/split-text";

interface WelcomeStageProps {
  docCount: number | null;
  online: boolean;
  onSubmit: (question: string) => void;
}

const SUGGESTIONS = [
  "How is the vector index built?",
  "What do the citation scores mean?",
  "Compare chunk sizes for retrieval",
];

export function WelcomeStage({ docCount, online, onSubmit }: WelcomeStageProps) {
  return (
    <div className="flex w-full flex-col items-center px-6 pt-[14vh] pb-16 text-center">
      <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
        {online
          ? `Local retrieval · ${docCount === null ? "…" : `${docCount} chunks`}`
          : "Backend offline · start the API on :8000"}
      </p>

      <h1 className="mt-8 text-5xl leading-tight font-semibold tracking-tight text-foreground md:text-6xl">
        <SplitText
          text="Ask the docs."
          splitType="words"
          delay={0.09}
          duration={0.55}
          ease="power4.out"
          from={{ opacity: 0, y: 26 }}
          to={{ opacity: 1, y: 0 }}
          tag="span"
          textAlign="left"
          className="block"
        />
      </h1>

      <p className="mt-5 max-w-md text-[15px] leading-relaxed text-muted-foreground">
        Answers from your documents — every claim pinned to a source you can
        open. Nothing leaves this machine.
      </p>

      <div className="mt-9 flex flex-wrap items-center justify-center gap-2">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onSubmit(q)}
            className="rounded-full border border-border bg-card px-3.5 py-1.5 font-mono text-[11px] text-muted-foreground transition-colors hover:border-ring/50 hover:text-foreground"
          >
            {q}
          </button>
        ))}
      </div>

      {!online && (
        <p className="mt-6 max-w-sm text-[13px] text-muted-foreground/80">
          The index answers nothing without the API. Start it with
          <code className="mx-1 rounded bg-secondary px-1.5 py-0.5 font-mono text-[11px] text-foreground">
            venv/bin/uvicorn app.main:app
          </code>
          from <code className="mx-1 rounded bg-secondary px-1.5 py-0.5 font-mono text-[11px] text-foreground">backend/</code>.
        </p>
      )}
    </div>
  );
}