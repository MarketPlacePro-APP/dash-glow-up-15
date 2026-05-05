import { BarChart3, CalendarClock, DollarSign, GraduationCap, Search, TrendingUp, Users, Youtube, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { useExecutiveMetrics } from "@/data/DashboardDataProvider";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

type Status = "green" | "yellow" | "red";

const statusClasses: Record<Status, string> = {
  green: "bg-success/15 text-success border-success/25",
  yellow: "bg-warning/15 text-warning border-warning/25",
  red: "bg-destructive/15 text-destructive border-destructive/25",
};

const MiniCard = ({ label, value, delta, icon: Icon, accent = false }: { label: string; value: number; delta: number; icon: typeof Users; accent?: boolean }) => (
  <div className={cn("rounded-xl border p-4 transition-all hover:-translate-y-0.5", accent ? "border-success/35 bg-success/10" : "border-border bg-card/60 hover:border-primary/30")}>
    <div className="flex items-center justify-between gap-2">
      <div className={cn("h-9 w-9 rounded-lg flex items-center justify-center", accent ? "bg-success/15 text-success" : "bg-primary/10 text-primary")}>
        <Icon className="h-4 w-4" />
      </div>
      <span className={cn("text-xs font-bold rounded-full px-2 py-0.5", delta >= 0 ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive")}>
        {delta >= 0 ? "+" : ""}{formatNumber(delta)}
      </span>
    </div>
    <p className="mt-4 text-[11px] font-semibold tracking-wide uppercase text-muted-foreground">{label}</p>
    <p className="text-3xl font-bold tracking-tight">{formatNumber(value)}</p>
  </div>
);

const ChannelIcon = ({ channel }: { channel: string }) => {
  if (channel === "Facebook") return <Users className="h-4 w-4" />;
  if (channel === "YouTube") return <Youtube className="h-4 w-4" />;
  if (channel === "Google Search") return <Search className="h-4 w-4" />;
  return <BarChart3 className="h-4 w-4" />;
};

export const ExecutiveOverview = () => {
  const metrics = useExecutiveMetrics();

  return (
    <PageShell
      eyebrow="EXECUTIVE OVERVIEW"
      title="TLWB KPI Dashboard"
      description={`Last updated: ${metrics.lastRefreshed}`}
    >
      <SectionCard eyebrow="Expo" title="May Investor Expo Count" subtitle="Buying Units, guests, and brand mix from latest available Expo count.">
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
          {metrics.expoCounts.map((item) => (
            <MiniCard
              key={item.label}
              label={item.label}
              value={item.value}
              delta={item.delta}
              icon={item.label === "Total" ? TrendingUp : item.label === "Guests" ? Users : Zap}
              accent={item.label === "Total"}
            />
          ))}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Active Preview"
        title="Atlanta + Norfolk session pace"
        subtitle="Completed/reported sessions so far; Sales % uses attendees before the 30-minute cutoff."
        action={<Link to="/preview" className="text-xs font-medium text-primary hover:underline">Open Preview →</Link>}
      >
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {metrics.activePreviewMarkets.map((market) => (
            <div key={market.market} className="rounded-xl border border-border bg-card/60 p-5 hover:border-primary/35 transition-all">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <h4 className="text-2xl font-bold tracking-tight">{market.market}</h4>
                  <p className="text-sm text-muted-foreground">{market.team}</p>
                </div>
                <span className={cn("border text-[10px] font-bold rounded-full px-2.5 py-1 uppercase", statusClasses[market.status])}>{market.status}</span>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                <Stat label="Sessions" value={`${market.sessionsCompleted} / ${market.totalSessions}`} />
                <Stat label="Reg so far" value={formatNumber(market.registered)} />
                <Stat label="Attendance" value={formatNumber(market.attendedCutoff)} />
                <Stat label="Sales" value={formatNumber(market.sales)} accent="success" />
                <Stat label="Preview Show %" value={formatPercent(market.previewShowRate)} accent={market.previewShowRate >= 0.15 ? "success" : "warning"} />
                <Stat label="Sales %" value={formatPercent(market.salesRate)} accent={market.salesRate >= 0.33 ? "success" : "warning"} />
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <SectionCard
          eyebrow="Middle-End"
          title="Recent show rates + next pipeline"
          subtitle="Executive summary only; full detail belongs on Workshop / ME."
          action={<Link to="/workshop" className="text-xs font-medium text-primary hover:underline">Open Workshop / ME →</Link>}
        >
          <div className="space-y-3">
            {metrics.middleEndSummary.map((row) => (
              <div key={`${row.market}-${row.team}`} className="rounded-xl border border-border bg-card/50 p-4 flex items-center gap-4 flex-wrap">
                <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center"><GraduationCap className="h-5 w-5" /></div>
                <div className="min-w-[170px] flex-1">
                  <p className="font-semibold">{row.market}</p>
                  <p className="text-xs text-muted-foreground">{row.team} · started {row.startDate}</p>
                </div>
                <Stat label="Sold" value={formatNumber(row.sold)} />
                <Stat label="Attended" value={formatNumber(row.attended)} />
                <Stat label="ME Show %" value={formatPercent(row.showRate)} accent="success" />
              </div>
            ))}
            <div className="rounded-xl border border-dashed border-warning/35 bg-warning/10 p-4 flex items-center justify-between gap-3 flex-wrap">
              <div>
                <p className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground">Upcoming ME Pipeline</p>
                <p className="text-lg font-bold">{metrics.upcomingMePipeline.market}</p>
                <p className="text-xs text-muted-foreground">Marked source pending until next ME pipeline refresh.</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-warning">{formatNumber(metrics.upcomingMePipeline.expected)}</p>
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">coming up</p>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Schedule"
          title="Upcoming route blocks"
          subtitle="Operational Schedule calendar remains available with Month / Week / List and team filters."
          action={<Link to="/schedule" className="text-xs font-medium text-primary hover:underline">Open Schedule →</Link>}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {metrics.data.scheduleRouteBlocks.filter((block) => block.status === "active" || block.status === "upcoming").slice(0, 4).map((block) => (
              <Link key={block.id} to="/schedule" className="rounded-xl border border-border bg-card/50 hover:bg-card transition-all p-4">
                <div className="flex items-center gap-2 mb-3"><CalendarClock className="h-4 w-4 text-primary" /><p className="font-semibold">{block.market}</p></div>
                <div className="grid grid-cols-2 gap-3">
                  <Stat label="Team" value={block.team} />
                  <Stat label="Events" value={block.eventCount} />
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard
        eyebrow="Active Marketing"
        title="Raleigh, Tampa, West Palm Beach"
        subtitle="Pre-event Event Stats only: regs, spend, and CPR by channel. Butt-in-seat counts are not shown before markets start."
        action={<Link to="/marketing" className="text-xs font-medium text-primary hover:underline">Open Marketing →</Link>}
      >
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {metrics.activeMarketingMarkets.map((market) => (
            <div key={market.market} className="rounded-xl border border-border bg-card/60 p-5 hover:border-primary/35 transition-all">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <h4 className="text-xl font-bold">{market.market}</h4>
                  <p className="text-xs text-muted-foreground">Starts {market.starts}</p>
                </div>
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              <div className="space-y-2">
                {market.channels.map((channel) => (
                  <div key={channel.channel} className={cn("rounded-lg border p-3", channel.channel === "Total" ? "border-success/25 bg-success/10" : "border-border bg-background/40")}>
                    <div className="flex items-center gap-2 mb-2 text-sm font-semibold"><ChannelIcon channel={channel.channel} />{channel.channel}</div>
                    <div className="grid grid-cols-3 gap-2">
                      <Stat label="Regs" value={formatNumber(channel.regs)} />
                      <Stat label="Spend" value={formatCurrency(channel.spend)} />
                      <Stat label="CPR" value={formatCurrency(channel.cpr)} accent={channel.channel === "Total" ? "success" : undefined} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </PageShell>
  );
};
