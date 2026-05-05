import { Megaphone, MapPin, DollarSign, Users, Activity } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

const summary = [
  { label: "Active Spend", value: "$35,840", sub: "Across 2 markets", icon: DollarSign, tone: "primary" },
  { label: "Active Regs", value: "1,512", sub: "Combined registrations", icon: Users, tone: "success" },
  { label: "Avg CPR", value: "$23.50", sub: "Cost per registration", icon: Activity, tone: "primary" },
  { label: "Workshops", value: "2", sub: "Live this cycle", icon: Megaphone, tone: "warning" },
];

const markets = [
  {
    name: "Minneapolis",
    workshops: 1,
    regs: 733,
    cpr: 24,
    spend: 17600,
    starts: "Sat May 16",
    pacing: 78,
    note: "Weekend push planned — emails warming.",
  },
  {
    name: "West Palm Beach",
    workshops: 1,
    regs: 779,
    cpr: 23,
    spend: 18240,
    starts: "Sat May 16",
    pacing: 84,
    note: "Strong digital response from FB + Direct mail.",
  },
];

const history = [
  { city: "Atlanta", finished: "Apr 26", regs: 712, cpr: 25, sales: 25 },
  { city: "Norfolk", finished: "Apr 19", regs: 540, cpr: 28, sales: 14 },
  { city: "Phoenix", finished: "Apr 12", regs: 690, cpr: 22, sales: 23 },
];

const toneClass: Record<string, string> = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
};

const Marketing = () => (
  <PageShell
    eyebrow="MARKETING"
    title="Active Markets & Spend"
    description="Workshop registrations, cost per reg, and spend pacing across all live markets."
  >
    <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
      {summary.map((s) => {
        const Icon = s.icon;
        return (
          <div
            key={s.label}
            className="glass border border-border rounded-xl p-4 hover:border-primary/40 transition-all"
          >
            <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}>
              <Icon className="h-4 w-4" />
            </div>
            <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
              {s.label}
            </p>
            <p className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.sub}</p>
          </div>
        );
      })}
    </section>

    <SectionCard
      eyebrow="Active Markets"
      title="Live cycles & spend pacing"
      subtitle="Diagnostic only — comparisons & forecasts in dedicated view."
      action={
        <button className="text-xs font-medium text-primary hover:underline">
          Comparisons / Forecasting →
        </button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {markets.map((m) => (
          <div
            key={m.name}
            className="rounded-xl border border-border bg-card/60 hover:border-primary/40 transition-all p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success/15 text-success text-[10px] font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft" />
                ACTIVE
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                <MapPin className="h-3 w-3" /> Starts {m.starts}
              </span>
            </div>
            <h4 className="text-xl font-bold">{m.name}</h4>
            <p className="text-xs text-muted-foreground mt-1">{m.note}</p>
            <div className="mt-4 grid grid-cols-4 gap-3">
              <Stat label="Workshops" value={m.workshops} />
              <Stat label="Regs" value={m.regs.toLocaleString()} />
              <Stat label="CPR" value={`$${m.cpr}`} accent="success" />
              <Stat label="Spend" value={`$${(m.spend / 1000).toFixed(1)}k`} />
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-1.5">
                <span>Spend pacing</span>
                <span className="font-semibold text-foreground">{m.pacing}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted/60 overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${m.pacing}%` }} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>

    <SectionCard eyebrow="History" title="Recently closed cycles">
      <div className="overflow-x-auto -mx-2">
        <table className="w-full text-sm min-w-[520px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-muted-foreground">
              <th className="text-left font-semibold px-2 py-2">Market</th>
              <th className="text-left font-semibold px-2 py-2">Finished</th>
              <th className="text-right font-semibold px-2 py-2">Regs</th>
              <th className="text-right font-semibold px-2 py-2">CPR</th>
              <th className="text-right font-semibold px-2 py-2">Sales</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.city} className="border-t border-border">
                <td className="px-2 py-3 font-semibold">{h.city}</td>
                <td className="px-2 py-3 text-muted-foreground">{h.finished}</td>
                <td className="px-2 py-3 text-right">{h.regs}</td>
                <td className="px-2 py-3 text-right text-success font-semibold">${h.cpr}</td>
                <td className="px-2 py-3 text-right">{h.sales}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  </PageShell>
);

export default Marketing;