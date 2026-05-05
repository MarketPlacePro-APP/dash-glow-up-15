import { useMemo, useState } from "react";
import { Eye, Percent, TrendingUp, Users } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { activePreviewMarkets } from "@/data/executiveAdapters";
import { previewSessions, teamPreviewHistory, type TeamPreviewHistoryRow } from "@/data/tlwbPageAdapters";
import { formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

const toneClass: Record<string, string> = { primary: "text-primary bg-primary/10", success: "text-success bg-success/10", warning: "text-warning bg-warning/10" };
const statusClasses: Record<string, string> = { green: "bg-success/15 text-success border-success/25", yellow: "bg-warning/15 text-warning border-warning/25", red: "bg-destructive/15 text-destructive border-destructive/25" };
const teams = ["Team Dent", "Team Vogel", "Team Wayne", "Team Wyman"] as const;

type Filter = "last6" | "year" | "all";

const teamRows = (team: TeamPreviewHistoryRow["team"], filter: Filter) => {
  const rows = teamPreviewHistory.filter((row) => row.team === team).sort((a, b) => b.date.localeCompare(a.date));
  if (filter === "last6") return rows.slice(0, 6);
  if (filter === "year") return rows.filter((row) => row.date >= "2025-05-05");
  return rows;
};

const totalRow = (rows: TeamPreviewHistoryRow[]) => {
  const reg = rows.reduce((acc, row) => acc + row.reg, 0);
  const attended = rows.reduce((acc, row) => acc + row.attended, 0);
  const sold = rows.reduce((acc, row) => acc + row.sold, 0);
  const workshop = rows.reduce((acc, row) => acc + (row.workshopAttendance ?? 0), 0);
  return { reg, attended, sold, showRate: reg ? attended / reg : 0, salesRate: attended ? sold / attended : 0, workshop };
};

const Preview = () => {
  const [filter, setFilter] = useState<Filter>("last6");
  const registered = activePreviewMarkets.reduce((acc, p) => acc + p.registered, 0);
  const attended = activePreviewMarkets.reduce((acc, p) => acc + p.attendedCutoff, 0);
  const sales = activePreviewMarkets.reduce((acc, p) => acc + p.sales, 0);
  const summary = [
    { label: "Active Markets", value: formatNumber(activePreviewMarkets.length), icon: Users, tone: "primary" },
    { label: "Reg So Far", value: formatNumber(registered), icon: Users, tone: "primary" },
    { label: "Preview Show %", value: formatPercent(registered ? attended / registered : 0), icon: Percent, tone: "warning" },
    { label: "Sales %", value: formatPercent(attended ? sales / attended : 0), icon: TrendingUp, tone: "success" },
  ];
  const sessionsByMarket = useMemo(() => previewSessions.reduce<Record<string, typeof previewSessions>>((acc, row) => {
    acc[row.market] = [...(acc[row.market] ?? []), row];
    return acc;
  }, {}), []);

  return (
    <PageShell eyebrow="PREVIEW" title="Active Preview" description="Atlanta / Team Vogel and Norfolk / Team Dent session performance, plus team historical benchmarks.">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
        {summary.map((s) => { const Icon = s.icon; return <div key={s.label} className="glass border border-border rounded-xl p-4"><div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}><Icon className="h-4 w-4" /></div><p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{s.label}</p><p className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</p></div>; })}
      </section>

      <SectionCard eyebrow="Active Current Markets" title="Atlanta + Norfolk" subtitle="Completed/reported sessions only. Sales % uses on-time attendees before the 30-minute cutoff.">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {activePreviewMarkets.map((market) => (
            <div key={market.market} className="rounded-xl border border-border bg-card/60 p-5 hover:border-primary/35 transition-all">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div><h4 className="text-2xl font-bold tracking-tight">{market.market}</h4><p className="text-sm text-muted-foreground">{market.team}</p></div>
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

      <SectionCard eyebrow="Session Breakdown" title="Reported sessions by active market" subtitle="Each market includes a total row for the run so far.">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {activePreviewMarkets.map((market) => {
            const rows = sessionsByMarket[market.market as "Atlanta" | "Norfolk"] ?? [];
            const totals = rows.reduce((acc, row) => ({ reg: acc.reg + row.reg, attendance: acc.attendance + row.attendance, sales: acc.sales + row.sales }), { reg: 0, attendance: 0, sales: 0 });
            return (
              <div key={`${market.market}-sessions`} className="rounded-xl border border-border bg-card/50 p-4 overflow-x-auto">
                <h4 className="font-bold mb-3">{market.market} — {market.team}</h4>
                <table className="w-full text-sm min-w-[520px]">
                  <thead><tr className="text-[10px] uppercase tracking-wide text-muted-foreground"><th className="text-left font-semibold py-2">Session</th><th className="text-right font-semibold py-2">Reg</th><th className="text-right font-semibold py-2">Attendance</th><th className="text-right font-semibold py-2">Sales</th><th className="text-right font-semibold py-2">Sales %</th></tr></thead>
                  <tbody>
                    {rows.map((row) => (<tr key={`${row.market}-${row.session}`} className="border-t border-border"><td className="py-3 font-semibold">{row.session}</td><td className="py-3 text-right">{formatNumber(row.reg)}</td><td className="py-3 text-right">{formatNumber(row.attendance)}</td><td className="py-3 text-right">{formatNumber(row.sales)}</td><td className="py-3 text-right font-semibold text-success">{formatPercent(row.attendance ? row.sales / row.attendance : 0)}</td></tr>))}
                    <tr className="border-t-2 border-primary/30 bg-primary/5"><td className="py-3 font-bold">Total so far</td><td className="py-3 text-right font-bold">{formatNumber(totals.reg)}</td><td className="py-3 text-right font-bold">{formatNumber(totals.attendance)}</td><td className="py-3 text-right font-bold">{formatNumber(totals.sales)}</td><td className="py-3 text-right font-bold text-success">{formatPercent(totals.attendance ? totals.sales / totals.attendance : 0)}</td></tr>
                  </tbody>
                </table>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Team Historical Performance"
        title="Last markets by speaker team"
        subtitle="Slack final/session posts where available; workshop attendance remains blank when ME has not completed or source is unavailable."
        action={<select value={filter} onChange={(event) => setFilter(event.target.value as Filter)} className="rounded-lg border border-border bg-background px-3 py-2 text-xs font-semibold"><option value="last6">Last 6 markets</option><option value="year">1 year</option><option value="all">All recent</option></select>}
      >
        <div className="space-y-5">
          {teams.map((team) => {
            const rows = teamRows(team, filter);
            const total = totalRow(rows);
            return (
              <div key={team} className="rounded-xl border border-border bg-card/50 p-4 overflow-x-auto">
                <h4 className="text-lg font-bold mb-3">{team}</h4>
                <table className="w-full text-sm min-w-[960px]">
                  <thead><tr className="text-[10px] uppercase tracking-wide text-muted-foreground"><th className="text-left font-semibold py-2">Market</th><th className="text-left font-semibold py-2">Date</th><th className="text-right font-semibold py-2">Reg</th><th className="text-right font-semibold py-2">Show-up</th><th className="text-right font-semibold py-2">Sales %</th><th className="text-right font-semibold py-2">Buying units</th><th className="text-right font-semibold py-2">Sold</th><th className="text-right font-semibold py-2">3-day WS attendance</th></tr></thead>
                  <tbody>
                    {rows.map((row) => (<tr key={`${row.team}-${row.market}-${row.date}`} className="border-t border-border"><td className="py-3 font-semibold">{row.market}</td><td className="py-3 text-muted-foreground">{row.date}</td><td className="py-3 text-right">{formatNumber(row.reg)}</td><td className="py-3 text-right">{formatPercent(row.showRate)}</td><td className="py-3 text-right font-semibold text-success">{formatPercent(row.salesRate)}</td><td className="py-3 text-right">{formatNumber(row.buyingUnits)}</td><td className="py-3 text-right">{formatNumber(row.sold)}</td><td className="py-3 text-right">{row.workshopAttendance === null ? "—" : formatNumber(row.workshopAttendance)}</td></tr>))}
                    <tr className="border-t-2 border-primary/30 bg-primary/5"><td className="py-3 font-bold">Total / weighted</td><td className="py-3 text-muted-foreground">{filter === "last6" ? "Last 6" : filter === "year" ? "1 year" : "All recent"}</td><td className="py-3 text-right font-bold">{formatNumber(total.reg)}</td><td className="py-3 text-right font-bold">{formatPercent(total.showRate)}</td><td className="py-3 text-right font-bold text-success">{formatPercent(total.salesRate)}</td><td className="py-3 text-right font-bold">{formatNumber(total.sold)}</td><td className="py-3 text-right font-bold">{formatNumber(total.sold)}</td><td className="py-3 text-right font-bold">{total.workshop ? formatNumber(total.workshop) : "—"}</td></tr>
                  </tbody>
                </table>
              </div>
            );
          })}
        </div>
      </SectionCard>
    </PageShell>
  );
};
export default Preview;
