import { Activity, DollarSign, Megaphone, Users } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { activeMarketingMarkets } from "@/data/executiveAdapters";
import { marketingHistory } from "@/data/tlwbPageAdapters";
import { formatCurrency, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

const toneClass: Record<string, string> = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
};

const fmtMaybeCurrency = (value: number | null) => (value === null ? "Source pending" : formatCurrency(value));
const fmtMaybeNumber = (value: number | null) => (value === null ? "Source pending" : formatNumber(value));
const totalChannel = (market: (typeof activeMarketingMarkets)[number]) => market.channels.find((channel) => channel.channel === "Total")!;

const Marketing = () => {
  const totals = activeMarketingMarkets.map(totalChannel);
  const spend = totals.reduce((acc, item) => acc + item.spend, 0);
  const regs = totals.reduce((acc, item) => acc + item.regs, 0);
  const avgCpr = regs ? spend / regs : 0;
  const summary = [
    { label: "Active Markets", value: formatNumber(activeMarketingMarkets.length), sub: "Raleigh, Tampa, West Palm Beach", icon: Megaphone, tone: "warning" },
    { label: "Active Spend", value: formatCurrency(spend), sub: "Across active markets", icon: DollarSign, tone: "primary" },
    { label: "Active Regs", value: formatNumber(regs), sub: "Combined registrations", icon: Users, tone: "success" },
    { label: "Average CPR", value: formatCurrency(avgCpr), sub: "Spend ÷ registrations", icon: Activity, tone: "primary" },
  ];

  return (
    <PageShell eyebrow="MARKETING" title="Active Marketing" description="Current Event Stats pacing plus recent market history for comparison. No pre-event button-seat metrics are shown.">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
        {summary.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="glass border border-border rounded-xl p-4 hover:border-primary/40 transition-all">
              <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}><Icon className="h-4 w-4" /></div>
              <p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{s.label}</p>
              <p className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{s.sub}</p>
            </div>
          );
        })}
      </section>

      <SectionCard eyebrow="Active Markets" title="Raleigh, Tampa, West Palm Beach" subtitle="Facebook, YouTube, Google Search, and blended total from latest Event Stats posts.">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {activeMarketingMarkets.map((market) => (
            <div key={market.market} className="rounded-xl border border-border bg-card/60 hover:border-primary/40 transition-all p-5">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <h4 className="text-xl font-bold">{market.market}</h4>
                  <p className="text-xs text-muted-foreground">Starts {market.starts}</p>
                </div>
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success/15 text-success text-[10px] font-semibold"><span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft" />ACTIVE</span>
              </div>
              <div className="space-y-2">
                {market.channels.map((channel) => (
                  <div key={channel.channel} className={cn("rounded-lg border p-3", channel.channel === "Total" ? "border-success/30 bg-success/10" : "border-border bg-background/40")}>
                    <p className="text-sm font-semibold mb-2">{channel.channel}</p>
                    <div className="grid grid-cols-3 gap-2">
                      <Stat label="Regs" value={formatNumber(channel.regs)} />
                      <Stat label="Spend" value={formatCurrency(channel.spend)} />
                      <Stat label="CPR" value={channel.regs === 0 ? "N/A" : formatCurrency(channel.cpr)} accent={channel.channel === "Total" ? "success" : undefined} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Market History" title="Last 3 comparable runs" subtitle="Quick comparison against recent same-city activity. Missing spend/CPR is explicitly marked source pending.">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {activeMarketingMarkets.map((market) => (
            <div key={`${market.market}-history`} className="rounded-xl border border-border bg-card/50 p-4">
              <h4 className="text-lg font-bold mb-3">{market.market}</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[520px]">
                  <thead><tr className="text-[10px] uppercase tracking-wide text-muted-foreground"><th className="text-left font-semibold py-2">Event date</th><th className="text-right font-semibold py-2">Regs</th><th className="text-right font-semibold py-2">Spend</th><th className="text-right font-semibold py-2">CPR</th></tr></thead>
                  <tbody>
                    {(marketingHistory[market.market] ?? []).map((row) => (
                      <tr key={`${row.market}-${row.eventDate}`} className="border-t border-border align-top">
                        <td className="py-3 pr-2"><p className="font-semibold">{row.eventDate}</p><p className="text-[11px] text-muted-foreground mt-1">{row.notes}</p></td>
                        <td className="py-3 text-right">{fmtMaybeNumber(row.registrations)}</td>
                        <td className="py-3 text-right">{fmtMaybeCurrency(row.spend)}</td>
                        <td className="py-3 text-right font-semibold text-success">{row.cpr === null ? "Source pending" : formatCurrency(row.cpr)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </PageShell>
  );
};

export default Marketing;
