import { Activity, PhoneCall, Target, TrendingUp } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

const summary = [
  { label: "Total Calls", value: "2,400", icon: PhoneCall, tone: "primary" },
  { label: "Sets", value: "163", icon: Target, tone: "primary" },
  { label: "Conversion", value: "6.8%", icon: TrendingUp, tone: "success" },
  { label: "YTD Sets", value: "4,128", icon: Activity, tone: "warning" },
];

const teams = [
  { team: "Team Travis", calls: 1284, sets: 92, conv: 7.2, trend: "+0.4%", agents: 6 },
  { team: "Team Curt", calls: 1116, sets: 71, conv: 6.4, trend: "-0.2%", agents: 5 },
];

const sessions = [
  { date: "May 5", session: "AM Block", calls: 412, sets: 31, conv: 7.5 },
  { date: "May 5", session: "PM Block", calls: 389, sets: 24, conv: 6.2 },
  { date: "May 4", session: "AM Block", calls: 401, sets: 28, conv: 7.0 },
  { date: "May 4", session: "PM Block", calls: 378, sets: 22, conv: 5.8 },
];

const toneClass: Record<string, string> = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
};

const InsideSales = () => (
  <PageShell
    eyebrow="INSIDE SALES"
    title="Team Performance"
    description="Team Travis vs. Team Curt — sessions, sets, and conversion."
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

    <SectionCard eyebrow="Teams" title="Weekly comparison">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {teams.map((t) => (
          <div key={t.team} className="rounded-xl border border-border bg-card/60 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                  <Activity className="h-4 w-4" />
                </div>
                <h4 className="font-semibold">{t.team}</h4>
              </div>
              <span
                className={cn(
                  "text-[10px] font-semibold rounded-full px-2 py-0.5",
                  t.trend.startsWith("+")
                    ? "bg-success/15 text-success"
                    : "bg-destructive/15 text-destructive"
                )}
              >
                {t.trend}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-4 gap-3">
              <Stat label="Agents" value={t.agents} />
              <Stat label="Calls" value={t.calls.toLocaleString()} />
              <Stat label="Sets" value={t.sets} />
              <Stat label="Conv" value={`${t.conv}%`} accent="success" />
            </div>
          </div>
        ))}
      </div>
    </SectionCard>

    <SectionCard eyebrow="Sessions" title="Numbers per session">
      <div className="overflow-x-auto -mx-2">
        <table className="w-full text-sm min-w-[480px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-muted-foreground">
              <th className="text-left font-semibold px-2 py-2">Date</th>
              <th className="text-left font-semibold px-2 py-2">Session</th>
              <th className="text-right font-semibold px-2 py-2">Calls</th>
              <th className="text-right font-semibold px-2 py-2">Sets</th>
              <th className="text-right font-semibold px-2 py-2">Conv</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s, i) => (
              <tr key={i} className="border-t border-border">
                <td className="px-2 py-3 font-semibold">{s.date}</td>
                <td className="px-2 py-3 text-muted-foreground">{s.session}</td>
                <td className="px-2 py-3 text-right">{s.calls}</td>
                <td className="px-2 py-3 text-right">{s.sets}</td>
                <td className="px-2 py-3 text-right text-success font-semibold">{s.conv}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  </PageShell>
);

export default InsideSales;