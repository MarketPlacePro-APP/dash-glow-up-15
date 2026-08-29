import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";

type StatusResponse = {
  data_through: string | null;
  schedule_through?: string | null;
  last_checked: string | null;
  last_published: string | null;
  next_scheduled_check: string | null;
  refresh_schedule_label: string;
  refresh: {
    status: "idle" | "queued" | "running" | "succeeded" | "no_change" | "failed";
    message: string;
    requested_at: string | null;
    started_at: string | null;
    completed_at: string | null;
  };
};

const displayTime = (value: string | null | undefined, dateOnly = false) => {
  if (!value) return "Not available";
  const parsed = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00-06:00`) : new Date(value);
  if (!Number.isFinite(parsed.valueOf())) return value;
  return new Intl.DateTimeFormat("en-US", dateOnly
    ? { timeZone: "America/Denver", month: "short", day: "numeric", year: "numeric" }
    : { timeZone: "America/Denver", month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short" }
  ).format(parsed);
};

export const RefreshControl = () => {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/status", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error(`Status unavailable (${response.status})`);
      setStatus(await response.json());
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Status unavailable");
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    const active = status?.refresh.status === "queued" || status?.refresh.status === "running";
    const timer = window.setInterval(() => void loadStatus(), active ? 15_000 : 60_000);
    return () => window.clearInterval(timer);
  }, [loadStatus, status?.refresh.status]);

  const requestRefresh = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/refresh", { method: "POST", credentials: "same-origin", headers: { "content-type": "application/json" } });
      const body = await response.json();
      if (!response.ok && response.status !== 429) throw new Error(body.error ?? `Refresh request failed (${response.status})`);
      await loadStatus();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Refresh request failed");
    } finally {
      setSubmitting(false);
    }
  };

  const active = status?.refresh.status === "queued" || status?.refresh.status === "running";
  const tone = useMemo(() => {
    if (error || status?.refresh.status === "failed") return "bg-destructive";
    if (active) return "bg-warning animate-pulse";
    return "bg-success";
  }, [active, error, status?.refresh.status]);

  return (
    <details className="relative group">
      <summary className="list-none cursor-pointer inline-flex items-center gap-2 h-10 px-3.5 rounded-lg border border-border bg-card hover:bg-muted/60 text-sm font-medium transition">
        <span className={cn("h-2.5 w-2.5 rounded-full", tone)} />
        <span className="hidden sm:inline">{active ? "Refreshing" : status ? `Published ${displayTime(status.last_published)}` : "Refresh status"}</span>
        <RefreshCw className={cn("h-4 w-4 text-muted-foreground", active && "animate-spin")} />
      </summary>
      <div className="absolute right-0 mt-2 w-[min(92vw,390px)] rounded-xl border border-border bg-popover p-4 shadow-xl z-50">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Dashboard freshness</p>
            <p className="mt-1 text-sm font-semibold">{status?.refresh.message ?? "Loading current status…"}</p>
          </div>
          <span className={cn("mt-1 h-3 w-3 shrink-0 rounded-full", tone)} />
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
          <div><dt className="text-muted-foreground">Data through</dt><dd className="mt-1 font-semibold">{displayTime(status?.data_through, true)}</dd></div>
          <div><dt className="text-muted-foreground">Last checked</dt><dd className="mt-1 font-semibold">{displayTime(status?.last_checked)}</dd></div>
          <div><dt className="text-muted-foreground">Last published</dt><dd className="mt-1 font-semibold">{displayTime(status?.last_published)}</dd></div>
          <div><dt className="text-muted-foreground">Next check</dt><dd className="mt-1 font-semibold">{displayTime(status?.next_scheduled_check)}</dd></div>
        </dl>
        <p className="mt-3 text-[11px] text-muted-foreground">{status?.refresh_schedule_label ?? "Hourly change-aware checks"}. Manual requests start within five minutes.</p>
        {error ? <p className="mt-3 text-xs font-semibold text-destructive">{error}</p> : null}
        <button
          type="button"
          onClick={() => void requestRefresh()}
          disabled={submitting || active || !status}
          className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw className={cn("h-4 w-4", (submitting || active) && "animate-spin")} />
          {active ? "Refresh in progress" : submitting ? "Queueing…" : "Refresh now"}
        </button>
      </div>
    </details>
  );
};