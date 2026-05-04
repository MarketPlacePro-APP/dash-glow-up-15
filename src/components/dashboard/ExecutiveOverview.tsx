import {
  Users,
  UserCheck,
  Briefcase,
  Building2,
  Key,
  Megaphone,
  Eye,
  TrendingUp,
  GraduationCap,
  CalendarClock,
  ArrowUpRight,
  MapPin,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "primary" | "success" | "warning" | "info";

const toneClasses: Record<Tone, { dot: string; icon: string; chip: string }> = {
  primary: { dot: "bg-primary", icon: "text-primary bg-primary/10", chip: "bg-primary/10 text-primary" },
  success: { dot: "bg-success", icon: "text-success bg-success/10", chip: "bg-success/15 text-success" },
  warning: { dot: "bg-warning", icon: "text-warning bg-warning/10", chip: "bg-warning/15 text-warning" },
  info: { dot: "bg-foreground/40", icon: "text-foreground bg-muted", chip: "bg-muted text-muted-foreground" },
};

const kpis = [
  { label: "BUs", value: "131", sub: "Expo strip", icon: Briefcase, tone: "info" as Tone, delta: "+8" },
  { label: "Guests", value: "53", sub: "Total: 184", icon: Users, tone: "info" as Tone, delta: "+12" },
  { label: "UTL", value: "42", sub: "Expo strip", icon: UserCheck, tone: "info" as Tone, delta: "+3" },
  { label: "TLWB", value: "88", sub: "Expo strip", icon: Building2, tone: "info" as Tone, delta: "+5" },
  { label: "KeySpire", value: "1", sub: "Expo strip", icon: Key, tone: "info" as Tone, delta: "—" },
];

const performanceKpis = [
  {
    label: "Active marketing",
    value: "1,512",
    sub: "$35,840 spend",
    icon: Megaphone,
    tone: "primary" as Tone,
    progress: 76,
  },
  {
    label: "Preview show %",
    value: "15.2%",
    sub: "126 / 830 attended",
    icon: Eye,
    tone: "warning" as Tone,
    progress: 15.2,
  },
  {
    label: "Preview sales %",
    value: "33.6%",
    sub: "39 sales / 116 on-time",
    icon: TrendingUp,
    tone: "success" as Tone,
    progress: 33.6,
  },
  {
    label: "ME show %",
    value: "79.1%",
    sub: "53 showed / 67 sold",
    icon: GraduationCap,
    tone: "success" as Tone,
    progress: 79.1,
  },
  {
    label: "Next ME pipeline",
    value: "140",
    sub: "May 8 · LI + Ft. Lauderdale",
    icon: CalendarClock,
    tone: "primary" as Tone,
    progress: 60,
  },
];

const markets = [
  {
    name: "Minneapolis",
    workshops: 1,
    regs: 733,
    cpr: 24,
    spend: 17600,
    starts: "Sat May 16",
  },
  {
    name: "West Palm Beach",
    workshops: 1,
    regs: 779,
    cpr: 23,
    spend: 18240,
    starts: "Sat May 16",
  },
];

const previews = [
  { city: "Norfolk", team: "Team Dent", reg: 372, attended: 48, sales: 14, pct: 30.4 },
  { city: "Atlanta", team: "Team Vogel", reg: 458, attended: 78, sales: 25, pct: 35.7 },
];

const middleEnd = [
  { city: "LA2", team: "Team Tony", sold: 38, showed: 30, pct: 78.9 },
  { city: "Phoenix", team: "Team Shaw / Megan", sold: 29, showed: 23, pct: 79.3 },
];

export const ExecutiveOverview = () => {
  return (
    <div className="px-6 lg:px-8 py-8 max-w-[1600px] mx-auto space-y-8">
      {/* Hero header */}
      <section className="relative overflow-hidden rounded-2xl glass border border-border p-6 lg:p-8 animate-fade-up">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none" />
        <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-success/15 text-success text-[11px] font-semibold">
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft" />
              Live · Reporting window open
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">
              Executive <span className="text-gradient">Overview</span>
            </h1>
            <p className="text-sm text-muted-foreground">
              Expo, active marketing, previews, Middle-End, schedule, and Inside Sales — all at a glance.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="h-10 px-4 rounded-lg border border-border bg-card hover:bg-muted/60 text-sm font-medium transition">
              Open Marketing
            </button>
            <button className="h-10 px-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-sm font-semibold transition inline-flex items-center gap-2 ring-glow">
              Quick actions <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Expo strip */}
      <section className="space-y-3 animate-fade-up">
        <SectionHeading
          eyebrow="Expo strip"
          title="Attendance breakdown"
          subtitle="Today's on-floor counts across BUs, Guests and partners."
        />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {kpis.map((k, i) => {
            const Icon = k.icon;
            return (
              <div
                key={k.label}
                className="group relative glass border border-border rounded-xl p-4 hover:border-primary/40 transition-all"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <div className="flex items-start justify-between">
                  <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClasses[k.tone].icon)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-muted-foreground bg-muted/50 rounded-md px-1.5 py-0.5">
                    {k.delta}
                  </span>
                </div>
                <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                  {k.label}
                </p>
                <p className="text-2xl font-bold tracking-tight mt-0.5">{k.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{k.sub}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Performance KPIs */}
      <section className="space-y-3 animate-fade-up">
        <SectionHeading
          eyebrow="Funnel performance"
          title="Pipeline velocity"
          subtitle="Marketing through Middle-End — current week."
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {performanceKpis.map((k) => {
            const Icon = k.icon;
            return (
              <div
                key={k.label}
                className="glass border border-border rounded-xl p-4 hover:border-primary/40 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClasses[k.tone].icon)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className={cn("text-[10px] font-semibold rounded-full px-2 py-0.5", toneClasses[k.tone].chip)}>
                    {k.tone === "success" ? "On track" : k.tone === "warning" ? "Watch" : "Active"}
                  </span>
                </div>
                <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                  {k.label}
                </p>
                <p className="text-2xl font-bold tracking-tight mt-0.5">{k.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{k.sub}</p>
                <div className="mt-3 h-1.5 rounded-full bg-muted/60 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      k.tone === "success" && "bg-success",
                      k.tone === "warning" && "bg-warning",
                      k.tone === "primary" && "bg-primary"
                    )}
                    style={{ width: `${Math.min(k.progress, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Marketing — Active Markets */}
      <section className="glass border border-border rounded-2xl p-6 animate-fade-up">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-5">
          <div>
            <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">MARKETING</p>
            <h3 className="text-lg font-bold">Active Markets</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Executive row only · open Marketing for detailed cards / history.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 text-[10px] font-semibold rounded-md bg-warning/15 text-warning">
              DIAGNOSTIC ONLY
            </span>
            <button className="text-xs font-medium text-primary hover:underline">
              Comparisons / Forecasting →
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {markets.map((m) => (
            <div
              key={m.name}
              className="group relative rounded-xl border border-border bg-card/60 hover:border-primary/40 hover:bg-card transition-all p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success/15 text-success text-[10px] font-semibold">
                    <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft" />
                    ACTIVE
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {m.workshops} workshop
                  </span>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                  <MapPin className="h-3 w-3" /> Starts {m.starts}
                </span>
              </div>
              <h4 className="text-xl font-bold">{m.name}</h4>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <Stat label="Regs" value={m.regs.toLocaleString()} />
                <Stat label="CPR" value={`$${m.cpr}`} accent="success" />
                <Stat label="Spend" value={`$${(m.spend / 1000).toFixed(1)}k`} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Two column: Preview + Middle End */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-up">
        <section className="glass border border-border rounded-2xl p-6">
          <SectionHeading
            eyebrow="Preview Summary"
            title="On-the-ground conversion"
            subtitle="Source-roll math lives in diagnostics."
          />
          <div className="mt-4 space-y-3">
            {previews.map((p) => (
              <Row
                key={p.city}
                title={p.city}
                subtitle={p.team}
                stats={[
                  { label: "Reg", value: p.reg },
                  { label: "Attended", value: p.attended },
                  { label: "Sales", value: p.sales },
                ]}
                highlight={{ label: "Sales %", value: `${p.pct}%`, tone: p.pct >= 33 ? "success" : "warning" }}
              />
            ))}
          </div>
        </section>

        <section className="glass border border-border rounded-2xl p-6">
          <SectionHeading
            eyebrow="Middle-End Current Ops"
            title="Show & sold this week"
            subtitle="Workshop page carries speaker / final-report fields."
          />
          <div className="mt-4 space-y-3">
            {middleEnd.map((m) => (
              <Row
                key={m.city}
                title={m.city}
                subtitle={m.team}
                stats={[
                  { label: "Sold", value: m.sold },
                  { label: "Showed", value: m.showed },
                ]}
                highlight={{
                  label: "Show %",
                  value: `${m.pct}%`,
                  tone: m.pct >= 75 ? "success" : "warning",
                }}
              />
            ))}
            <div className="rounded-xl border border-dashed border-border p-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-muted-foreground">NEXT ME WEEK</p>
                <p className="text-sm font-semibold">Long Island + Fort Lauderdale</p>
                <p className="text-xs text-muted-foreground">May 8 pipeline</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">140</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Sold · pending</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Inside Sales strip */}
      <section className="glass border border-border rounded-2xl p-6 animate-fade-up">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-5">
          <div>
            <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">INSIDE SALES</p>
            <h3 className="text-lg font-bold">Weekly Strip</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Team Travis vs. Team Curt · prior-week comparison.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 text-[10px] font-semibold rounded-md bg-muted text-muted-foreground">
              SHEET · NUMBERS PER SESSION
            </span>
            <button className="h-9 px-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold transition inline-flex items-center gap-1.5">
              Open Inside Sales <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { team: "Team Travis", calls: 1284, sets: 92, conv: 7.2, trend: "+0.4%" },
            { team: "Team Curt", calls: 1116, sets: 71, conv: 6.4, trend: "-0.2%" },
          ].map((t) => (
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
                    t.trend.startsWith("+") ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive"
                  )}
                >
                  {t.trend}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <Stat label="Calls" value={t.calls.toLocaleString()} />
                <Stat label="Sets" value={t.sets} />
                <Stat label="Conv" value={`${t.conv}%`} accent="success" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="text-center text-[11px] text-muted-foreground py-4">
        TLWB Operations · Refreshed live · Source freshness in Data QA
      </p>
    </div>
  );
};

const SectionHeading = ({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) => (
  <div>
    <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">
      {eyebrow.toUpperCase()}
    </p>
    <h3 className="text-lg font-bold leading-tight">{title}</h3>
    {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
  </div>
);

const Stat = ({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: "success" | "warning";
}) => (
  <div>
    <p className="text-[10px] font-semibold tracking-wide uppercase text-muted-foreground">
      {label}
    </p>
    <p
      className={cn(
        "text-base font-bold mt-0.5",
        accent === "success" && "text-success",
        accent === "warning" && "text-warning"
      )}
    >
      {value}
    </p>
  </div>
);

const Row = ({
  title,
  subtitle,
  stats,
  highlight,
}: {
  title: string;
  subtitle: string;
  stats: { label: string; value: number | string }[];
  highlight: { label: string; value: string; tone: "success" | "warning" };
}) => (
  <div className="rounded-xl border border-border bg-card/50 hover:bg-card transition-all p-4 flex items-center gap-4 flex-wrap">
    <div className="min-w-[140px]">
      <p className="font-semibold">{title}</p>
      <p className="text-xs text-muted-foreground">{subtitle}</p>
    </div>
    <div className="flex-1 grid grid-cols-3 gap-3 min-w-[200px]">
      {stats.map((s) => (
        <Stat key={s.label} label={s.label} value={s.value} />
      ))}
    </div>
    <div
      className={cn(
        "px-3 py-2 rounded-lg text-right min-w-[90px]",
        highlight.tone === "success" ? "bg-success/10" : "bg-warning/10"
      )}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {highlight.label}
      </p>
      <p
        className={cn(
          "text-lg font-bold",
          highlight.tone === "success" ? "text-success" : "text-warning"
        )}
      >
        {highlight.value}
      </p>
    </div>
  </div>
);