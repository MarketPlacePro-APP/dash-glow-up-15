import { Eye, TrendingUp, Users, Percent } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

const summary = [
  { label: "Registered", value: "830", icon: Users, tone: "primary" },
  { label: "Attended", value: "126", icon: Eye, tone: "primary" },
  { label: "Show %", value: "15.2%", icon: Percent, tone: "warning" },
  { label: "Sales %", value: "33.6%", icon: TrendingUp, tone: "success" },
];

const previews = [
  { city: "Norfolk", team: "Team Dent", reg: 372, attended: 48, sales: 14, pct: 30.4 },
  { city: "Atlanta", team: "Team Vogel", reg: 458, attended: 78, sales: 25, pct: 35.7 },
  { city: "Tampa", team: "Team Vogel", reg: 410, attended: 62, sales: 18, pct: 29.0 },
  { city: "Houston", team: "Team Dent", reg: 388, attended: 55, sales: 21, pct: 38.2 },
];

const toneClass: Record<string, string> = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
};

const Preview = () => (
  <PageShell
    eyebrow="PREVIEW"
    title="Preview Conversion"
    description="On-the-ground attendance and sales conversion across active preview cities."
  >
    <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
      {summary.map((s) => {
        const Icon = s.icon;
        return (
          <div key={s.label} className="glass border border-border rounded-xl p-4">
            <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}>
              <Icon className="h-4 w-4" />
            </div>
            <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
              {s.label}
            </p>
            <p className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</p>
          </div>
        );
      })}
    </section>

    <SectionCard
      eyebrow="Preview Sessions"
      title="By city & team"
      subtitle="Source-roll math available in Data QA."
    >
      <div className="space-y-3">
        {previews.map((p) => (
          <div
            key={p.city}
            className="rounded-xl border border-border bg-card/50 hover:bg-card transition-all p-4 flex items-center gap-4 flex-wrap"
          >
            <div className="min-w-[160px]">
              <p className="font-semibold">{p.city}</p>
              <p className="text-xs text-muted-foreground">{p.team}</p>
            </div>
            <div className="flex-1 grid grid-cols-3 gap-3 min-w-[200px]">
              <Stat label="Reg" value={p.reg} />
              <Stat label="Attended" value={p.attended} />
              <Stat label="Sales" value={p.sales} />
            </div>
            <div
              className={cn(
                "px-3 py-2 rounded-lg text-right min-w-[100px]",
                p.pct >= 33 ? "bg-success/10" : "bg-warning/10"
              )}
            >
              <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Sales %
              </p>
              <p
                className={cn(
                  "text-base font-bold",
                  p.pct >= 33 ? "text-success" : "text-warning"
                )}
              >
                {p.pct}%
              </p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  </PageShell>
);

export default Preview;