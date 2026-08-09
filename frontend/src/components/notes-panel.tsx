"use client";

import { useEffect, useState } from "react";
import { FilePlus, Trash2 } from "lucide-react";

interface Note {
  id: string;
  title: string;
  body: string;
  updatedAt: number;
}

const STORAGE_KEY = "domainrag.notes.v1";

function readNotes(): Note[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NotesPanel() {
  const [notes, setNotes] = useState<Note[]>(() => {
    if (typeof window === "undefined") return [];
    return readNotes();
  });
  const [activeId, setActiveId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return readNotes()[0]?.id ?? null;
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
    } catch {
      /* storage full or unavailable — notes stay in memory for this session */
    }
  }, [notes]);

  const active = notes.find((n) => n.id === activeId) ?? null;

  const createNote = () => {
    const note: Note = {
      id: crypto.randomUUID(),
      title: "",
      body: "",
      updatedAt: Date.now(),
    };
    setNotes((prev) => [note, ...prev]);
    setActiveId(note.id);
  };

  const updateNote = (id: string, patch: Partial<Pick<Note, "title" | "body">>) => {
    setNotes((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, ...patch, updatedAt: Date.now() } : n
      )
    );
  };

  const deleteNote = (id: string) => {
    setNotes((prev) => {
      const rest = prev.filter((n) => n.id !== id);
      if (activeId === id) setActiveId(rest[0]?.id ?? null);
      return rest;
    });
  };

  const wordCount = active ? active.body.trim().split(/\s+/).filter(Boolean).length : 0;

  return (
    <div className="flex h-full min-h-0">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border">
        <div className="flex items-center justify-between px-4 py-3">
          <h2 className="font-mono text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Notes · {notes.length}
          </h2>
          <button
            type="button"
            onClick={createNote}
            title="New note"
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <FilePlus size={15} />
          </button>
        </div>
        <div className="custom-scrollbar flex-1 overflow-y-auto px-2 pb-3">
          {notes.length === 0 && (
            <p className="px-2 pt-2 font-mono text-[11px] leading-relaxed text-muted-foreground/70">
              No notes yet — add one to start studying.
            </p>
          )}
          {notes.map((n) => (
            <div
              key={n.id}
              className={`group flex w-full items-start gap-1 rounded-md px-2 py-2 text-left transition-colors ${
                n.id === activeId ? "bg-secondary" : "hover:bg-secondary/50"
              }`}
            >
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => setActiveId(n.id)}
              >
                <div className="truncate text-[13px] font-medium text-foreground">
                  {n.title.trim() || "Untitled note"}
                </div>
                <div className="truncate font-mono text-[10px] text-muted-foreground">
                  {formatTime(n.updatedAt)}
                </div>
              </button>
              <button
                type="button"
                onClick={() => deleteNote(n.id)}
                title="Delete note"
                className="mt-0.5 hidden rounded p-1 text-muted-foreground transition-colors hover:bg-border hover:text-destructive group-hover:block"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      <section className="flex min-h-0 flex-1 flex-col">
        {!active ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <p className="text-sm text-muted-foreground">
              Nothing open. Start a note from the sidebar.
            </p>
          </div>
        ) : (
          <>
            <input
              value={active.title}
              onChange={(e) => updateNote(active.id, { title: e.target.value })}
              placeholder="Title"
              aria-label="Note title"
              className="w-full border-b border-border bg-transparent px-5 py-3.5 text-[17px] font-semibold text-foreground outline-none placeholder:text-muted-foreground/50"
            />
            <textarea
              value={active.body}
              onChange={(e) => updateNote(active.id, { body: e.target.value })}
              placeholder="Write your notes here — saved locally in your browser."
              aria-label="Note body"
              className="custom-scrollbar min-h-0 flex-1 resize-none bg-transparent px-5 py-4 text-[15px] leading-relaxed text-foreground outline-none placeholder:text-muted-foreground/50"
            />
            <div className="flex items-center justify-between border-t border-border px-5 py-2">
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
                Saved to your browser · {wordCount} words
              </span>
              <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
                {formatTime(active.updatedAt)}
              </span>
            </div>
          </>
        )}
      </section>
    </div>
  );
}