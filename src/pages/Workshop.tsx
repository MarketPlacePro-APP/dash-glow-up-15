import { GraduationCap, Users, Percent, CalendarClock } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

const summary = [
  { label: "Sold", value: "67", icon: GraduationCap, tone: "primary" },
  { label: "Showed", value: "53", icon: Users, tone: "primary" },
  { label: "Show %", value: "79.1%", icon: Percent, tone: "success" },
  { label: "Next ME Pipeline", value: "140", icon: CalendarClock, tone: "warning" },
];

const middleEnd = [
  { city: "LA2", team: "Team Tony", sold: 38, showed: 30, pct: 78.9, speaker: "T. Reynolds" },
  { city: "Phoenix", team: "Team Shaw / Megan", sold: 29, showed: 23, pct: 79.3, speaker: "M. Clark" },
];

const upcoming = [
  { city: "Long Island", date: "May 8", sold: 78, speaker: "T. Reynolds" },
  { city: "Fort Lauderdale", date: "May 8", sold: 62, speaker: "M. Clark" },
];

const toneClass: Record<string, string> = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
};

const Workshop = () => (
  <PageShell
    eyebrow="WORKSHOP / MIDDLE-END"
    title="Show & Sold Performance"
    description="Current ME attendance, speaker assignments, and next-week pipeline."
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

    <SectionCard eyebrow="Current Ops" title="This week's ME sessions">
      <div className="space-y-3">
        {middleEnd.map((m) => (
          <div
            key={m.city}
            className="rounded-xl border border-border bg-card/50 hover:bg-card transition-all p-4 flex items-center gap-4 flex-wrap"
          >
            <div className="min-w-[160px]">
              <p className="font-semibold">{m.city}</p>
              <p className="text-xs text-muted-foreground">{m.team}</p>
            </div>
            <div className="flex-1 grid grid-cols-3 gap-3 min-w-[200px]">
              <Stat label="Sold" value={m.sold} />
              <Stat label="Showed" value={m.showed} />
              <Stat label="Speaker" value={m.speaker} />
            </div>
            <div
              className={cn(
                "px-3 py-2 rounded-lg text-right min-w-[100px]",
                m.pct >= 75 ? "bg-success/10" : "bg-warning/10"
              )}
            >
              <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Show %
              </p>
              <p
                className={cn(
                  "text-base font-bold",
                  m.pct >= 75 ? "text-success" : "text-warning"
                )}
              >
                {m.pct}%
              </p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>

    <SectionCard eyebrow="Pipeline" title="Next ME week — May 8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {upcoming.map((u) => (
          <div
            key={u.city}
            className="rounded-xl border border-dashed border-border p-5 hover:border-primary/40 transition-all"
          >
            <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">
              {u.date}
            </p>
            <h4 className="text-xl font-bold mt-1">{u.city}</h4>
            <p className="text-xs text-muted-foreground mt-1">Speaker: {u.speaker}</p>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Sold (pending)</p>
                <p className="text-3xl font-bold">{u.sold}</p>
              </div>
              <span className="px-2 py-1 text-[10px] font-semibold rounded-md bg-warning/15 text-warning">
                PENDING
              </span>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  </PageShell>
);

export default Workshop;