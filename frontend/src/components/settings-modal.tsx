"use client";

import { useState, useEffect } from "react";
import { X, Loader2, RefreshCw, Check, AlertCircle } from "lucide-react";
import {
  getModels,
  setModel,
  resetModel,
  ModelsResponse,
} from "@/lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: (model: string) => void;
}

export function SettingsModal({ open, onClose, onSaved }: Props) {
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [model, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      try {
        const m = await getModels();
        if (cancelled) return;
        setModels(m);
        setProvider(m.current.provider);
        setModelName(m.current.model);
        setBaseUrl(m.current.base_url);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load models");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open]);

  if (!open) return null;

  const providerInfo = models?.providers[provider];
  const isLocal = provider === "ollama";
  const modelSuggestions = isLocal
    ? (models?.local ?? [])
    : (providerInfo?.models ?? []);

  const handleSave = async () => {
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const status = await setModel({
        provider,
        model: model.trim(),
        api_key: isLocal ? "" : apiKey.trim(),
        base_url: provider === "custom" ? baseUrl.trim() : "",
      });
      setSaved(true);
      onSaved(`${status.provider}:${status.model}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update model");
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    setBusy(true);
    setError("");
    try {
      const status = await resetModel();
      setProvider(status.provider);
      setModelName(status.model);
      setBaseUrl(status.base_url);
      setApiKey("");
      setSaved(true);
      onSaved(`${status.provider}:${status.model}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to reset model");
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
          <h2 className="text-sm font-semibold tracking-wide">Model Settings</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-secondary text-muted-foreground transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <Separator />

        <div className="px-5 py-4 space-y-4">
          {busy && !models ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                  Provider
                </label>
                <select
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value);
                    setError("");
                    const info = models?.providers[e.target.value];
                    if (info?.models?.length) setModelName(info.models[0]);
                    if (e.target.value === "custom") setBaseUrl("");
                  }}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-muted-foreground/50"
                >
                  <option value="ollama">Ollama (local, free)</option>
                  {models &&
                    Object.entries(models.providers).map(([key, info]) => (
                      <option key={key} value={key}>
                        {info.label}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                  Model
                </label>
                <Input
                  list="model-suggestions"
                  value={model}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder={isLocal ? "e.g. qwen2.5:7b" : "e.g. gpt-4o-mini"}
                />
                <datalist id="model-suggestions">
                  {modelSuggestions.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>

              {!isLocal && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                    API Key
                  </label>
                  <Input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    autoComplete="off"
                  />
                  <p className="text-[11px] text-muted-foreground/60 mt-1">
                    Stored in memory only — never saved to disk or returned by the API.
                  </p>
                </div>
              )}

              {provider === "custom" && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                    Base URL
                  </label>
                  <Input
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="https://your-provider.example/v1"
                  />
                </div>
              )}

              {error && (
                <div className="flex items-start gap-2 rounded-md bg-destructive/10 text-destructive px-3 py-2 text-xs">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <span className="break-all">{error}</span>
                </div>
              )}

              {saved && (
                <div className="flex items-center gap-2 rounded-md bg-emerald-500/10 text-emerald-600 px-3 py-2 text-xs">
                  <Check size={14} />
                  <span>Model updated. New answers will use it.</span>
                </div>
              )}
            </>
          )}
        </div>

        <Separator />
        <div className="flex items-center justify-between px-5 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={busy || isLocal}
            className="flex items-center gap-1.5"
          >
            <RefreshCw size={14} />
            Reset to local
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={busy || !model.trim()}>
              {busy ? <Loader2 size={14} className="animate-spin" /> : "Save & apply"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
