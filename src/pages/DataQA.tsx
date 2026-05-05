import { ShieldCheck, AlertTriangle, RefreshCw, Database } from "lucide-react";
import { PageShell, SectionCard } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

const sources = [
  { name: "Marketing CRM", status: "fresh", lastSync: "2 min ago", rows: 12840 },
  { name: "Preview Attendance Sheet", status: "fresh", lastSync: "5 min ago", rows: 830 },
  { name: "Inside Sales Dialer", status: "fresh", lastSync: "1 min ago", rows: 2400 },
  { name: "Workshop Roster", status: "stale", lastSync: "3 hr ago", rows: 67 },
  { name: "Speaker Reports", status: "warn", lastSync: "45 min ago", rows: 12 },
];

const statusStyle: Record<string, { dot: string; chip: string; label: string }> = {
  fresh: { dot: "bg-success", chip: "bg-success/15 text-success", label: "Fresh" },
  warn: { dot: "bg-warning", chip: "bg-warning/15 text-warning", label: "Stale soon" },
  stale: { dot: "bg-destructive", chip: "bg-destructive/15 text-destructive", label: "Stale" },
};

const DataQA = () => (
  <PageShell
    eyebrow="DATA QA"
    title="Source Freshness & Health"
    description="Confirm every dashboard input is current before relying on numbers."
  >
    <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
      <Tile icon={ShieldCheck} label="Sources Healthy" value="3 / 5" tone="success" />
      <Tile icon={AlertTriangle} label="Needs Review" value="2" tone="warning" />
      <Tile icon={RefreshCw} label="Avg Sync" value="< 10 min" tone="primary" />
      <Tile icon={Database} label="Total Rows" value="16,149" tone="primary" />
    </section>

    <SectionCard eyebrow="Sources" title="All connected feeds">
      <div className="space-y-3">
        {sources.map((s) => {
          const sty = statusStyle[s.status];
          return (
            <div
              key={s.name}
              className="rounded-xl border border-border bg-card/50 hover:bg-card transition-all p-4 flex items-center gap-4 flex-wrap"
            >
              <div className="flex items-center gap-3 min-w-[220px]">
                <span className={cn("h-2.5 w-2.5 rounded-full animate-pulse-soft", sty.dot)} />
                <p className="font-semibold">{s.name}</p>
              </div>
              <div className="flex-1 grid grid-cols-2 gap-3 min-w-[200px]">
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground font-semibold">
                    Last sync
                  </p>
                  <p className="text-sm font-semibold mt-0.5">{s.lastSync}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground font-semibold">
                    Rows
                  </p>
                  <p className="text-sm font-semibold mt-0.5">{s.rows.toLocaleString()}</p>
                </div>
              </div>
              <span
                className={cn(
                  "text-[10px] font-semibold rounded-full px-2.5 py-1",
                  sty.chip
                )}
              >
                {sty.label}
              </span>
            </div>
          );
        })}
      </div>
    </SectionCard>
  </PageShell>
);

const Tile = ({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof ShieldCheck;
  label: string;
  value: string;
  tone: "primary" | "success" | "warning";
}) => {
  const tones: Record<string, string> = {
    primary: "text-primary bg-primary/10",
    success: "text-success bg-success/10",
    warning: "text-warning bg-warning/10",
  };
  return (
    <div className="glass border border-border rounded-xl p-4">
      <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", tones[tone])}>
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
        {label}
      </p>
      <p className="text-2xl font-bold tracking-tight mt-0.5">{value}</p>
    </div>
  );
};

export default DataQA;