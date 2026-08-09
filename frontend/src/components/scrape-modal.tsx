"use client";

import { useState } from "react";
import { X, Loader2, Globe, Check, AlertCircle } from "lucide-react";
import { scrapeUrl } from "@/lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ScrapeModal({ open, onClose }: Props) {
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ saved: string[]; skipped: string[]; documents: number } | null>(null);

  if (!open) return null;

  const handleScrape = async () => {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await scrapeUrl(url.trim(), maxPages);
      setResult({
        saved: res.saved,
        skipped: res.skipped.map((s) => `${s.url} (${s.reason})`),
        documents: res.documents,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scraping failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl border border-border bg-background shadow-xl animate-message-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4">
          <h2 className="text-sm font-semibold tracking-wide flex items-center gap-2">
            <Globe size={16} />
            Scrape a Web Page
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-secondary text-muted-foreground transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <Separator />

        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">
              URL
            </label>
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/docs/page"
              onKeyDown={(e) => {
                if (e.key === "Enter" && url.trim() && !busy) handleScrape();
              }}
            />
            <p className="text-[11px] text-muted-foreground/60 mt-1">
              The page is fetched, converted to markdown, and added to the knowledge base.
            </p>
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">
              Pages to fetch (1–10)
            </label>
            <Input
              type="number"
              min={1}
              max={10}
              value={maxPages}
              onChange={(e) =>
                setMaxPages(Math.max(1, Math.min(10, Number(e.target.value) || 1)))
              }
            />
            <p className="text-[11px] text-muted-foreground/60 mt-1">
              With more than 1, linked pages on the same domain are crawled first.
            </p>
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-md bg-destructive/10 text-destructive px-3 py-2 text-xs">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <span className="break-all">{error}</span>
            </div>
          )}

          {result && (
            <div className="rounded-md bg-emerald-500/10 text-emerald-600 px-3 py-2 text-xs space-y-1">
              <div className="flex items-center gap-2">
                <Check size={14} />
                <span>
                  Added {result.saved.length} page{result.saved.length === 1 ? "" : "s"} — knowledge
                  base now has {result.documents.toLocaleString()} chunks.
                </span>
              </div>
              {result.saved.map((s) => (
                <p key={s} className="pl-6 break-all text-emerald-700">
                  {s}
                </p>
              ))}
              {result.skipped.length > 0 && (
                <p className="pl-6 text-muted-foreground">
                  Skipped {result.skipped.length}: {result.skipped.join("; ")}
                </p>
              )}
            </div>
          )}
        </div>

        <Separator />
        <div className="flex items-center justify-end gap-2 px-5 py-4">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={busy}>
            Close
          </Button>
          <Button size="sm" onClick={handleScrape} disabled={busy || !url.trim()}>
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Globe size={14} />}
            {busy ? "Scraping..." : "Scrape & add"}
          </Button>
        </div>
      </div>
    </div>
  );
}