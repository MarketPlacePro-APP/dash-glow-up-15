import { useState } from "react";
import { CalendarClock, DollarSign, GraduationCap, Percent, Users } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { currentMiddleEndWorkshops, middleEndHistory, type MiddleEndHistoricalRow } from "@/data/tlwbPageAdapters";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

const toneClass: Record<string, string> = { primary: "text-primary bg-primary/10", success: "text-success bg-success/10", warning: "text-warning bg-warning/10" };
const teams = ["Team Tony", "Team Drexel", "Team Shaw", "Team Nick"] as const;
type Filter = "last6" | "ytd";

const fmtMoney = (value: number | null) => value === null ? "N/A" : formatCurrency(value);
const fmtNumber = (value: number | null) => value === null ? "N/A" : formatNumber(value);
const fmtPercentMaybe = (numerator: number | null, denominator: number) => numerator === null || !denominator ? "N/A" : formatPercent(numerator / denominator);
const perBu = (value: number | null, bu: number) => value === null || !bu ? "N/A" : formatCurrency(value / bu);

const rowsForTeam = (team: MiddleEndHistoricalRow["team"], filter: Filter) => {
  const rows = middleEndHistory.filter((row) => row.team === team).filter((row) => filter === "last6" || row.date >= "2026-01-01");
  return rows.sort((a, b) => b.date.localeCompare(a.date)).slice(0, filter === "last6" ? 6 : undefined);
};

const totalsFor = (rows: MiddleEndHistoricalRow[]) => {
  const buyingUnits = rows.reduce((acc, row) => acc + row.buyingUnits, 0);
  const closed = rows.reduce((acc, row) => acc + (row.soldClosed ?? 0), 0);
  const writtenKnown = rows.filter((row) => row.totalWritten !== null);
  const collectedKnown = rows.filter((row) => row.totalCollected !== null);
  const written = writtenKnown.reduce((acc, row) => acc + (row.totalWritten ?? 0), 0);
  const collected = collectedKnown.reduce((acc, row) => acc + (row.totalCollected ?? 0), 0);
  return { buyingUnits, closed: writtenKnown.length || collectedKnown.length ? closed : null, written: writtenKnown.length ? written : null, collected: collectedKnown.length ? collected : null };
};

const Workshop = () => {
  const [filter, setFilter] = useState<Filter>("last6");
  const buyingUnits = currentMiddleEndWorkshops.reduce((acc, row) => acc + row.buyingUnits, 0);
  const showed = currentMiddleEndWorkshops.reduce((acc, row) => acc + row.showed, 0);
  const summary = [
    { label: "Current Workshops", value: formatNumber(currentMiddleEndWorkshops.length), icon: CalendarClock, tone: "primary" },
    { label: "Buying Units", value: formatNumber(buyingUnits), icon: GraduationCap, tone: "primary" },
    { label: "Showed", value: formatNumber(showed), icon: Users, tone: "success" },
    { label: "Show %", value: formatPercent(buyingUnits ? showed / buyingUnits : 0), icon: Percent, tone: "success" },
  ];

  return (
    <PageShell eyebrow="WORKSHOP / MIDDLE-END" title="Workshop & Middle-End" description="Current ME show-up, final workshop fields, and team history. Unavailable ABC/collections fields stay N/A until final ME sources are connected.">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
        {summary.map((s) => { const Icon = s.icon; return <div key={s.label} className="glass border border-border rounded-xl p-4"><div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}><Icon className="h-4 w-4" /></div><p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{s.label}</p><p className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</p></div>; })}
      </section>

      <SectionCard eyebrow="Current / Just Completed" title="Team Tony — LA and Team Shaw — Phoenix" subtitle="Show-up is sourced from recent ME check-ins; final written/collected/ABC detail remains source pending.">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {currentMiddleEndWorkshops.map((row) => {
            const showRate = row.buyingUnits ? row.showed / row.buyingUnits : 0;
            return <div key={`${row.team}-${row.market}`} className="rounded-xl border border-border bg-card/60 p-5 hover:border-primary/35 transition-all"><div className="flex items-start justify-between gap-3 mb-4"><div><h4 className="text-2xl font-bold tracking-tight">{row.market}</h4><p className="text-sm text-muted-foreground">{row.team} · {row.eventDate}</p></div><span className="rounded-full border border-warning/30 bg-warning/10 px-2.5 py-1 text-[10px] font-bold uppercase text-warning">finals pending</span></div><div className="grid grid-cols-2 lg:grid-cols-4 gap-3"><Stat label="Buying units" value={formatNumber(row.buyingUnits)} /><Stat label="Sold / closed" value={fmtNumber(row.soldClosed)} /><Stat label="Showed" value={formatNumber(row.showed)} accent="success" /><Stat label="Show %" value={formatPercent(showRate)} accent="success" /><Stat label="Total written" value={fmtMoney(row.totalWritten)} /><Stat label="Total collected" value={fmtMoney(row.totalCollected)} /><Stat label="Written / BU" value={perBu(row.totalWritten, row.buyingUnits)} /><Stat label="Collected / BU" value={perBu(row.totalCollected, row.buyingUnits)} /><Stat label="ABC mix" value={row.abcBreakdown ?? "N/A"} /><Stat label="Close % buyers" value={fmtPercentMaybe(row.soldClosed, row.buyingUnits)} /></div><p className="mt-4 text-xs text-muted-foreground">{row.notes}</p></div>;
          })}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Historical ME Performance" title="Team history" subtitle="Last 6 final markets by default. Fields without final workshop/ME source remain N/A."
        action={<select value={filter} onChange={(event) => setFilter(event.target.value as Filter)} className="rounded-lg border border-border bg-background px-3 py-2 text-xs font-semibold"><option value="last6">Last 6 markets</option><option value="ytd">Year to date</option></select>}
      >
        <div className="space-y-5">
          {teams.map((team) => {
            const rows = rowsForTeam(team, filter);
            const total = totalsFor(rows);
            return <div key={team} className="rounded-xl border border-border bg-card/50 p-4 overflow-x-auto"><h4 className="text-lg font-bold mb-3">{team}</h4><table className="w-full text-sm min-w-[1120px]"><thead><tr className="text-[10px] uppercase tracking-wide text-muted-foreground"><th className="text-left font-semibold py-2">Market</th><th className="text-left font-semibold py-2">Date</th><th className="text-right font-semibold py-2">Buying units</th><th className="text-right font-semibold py-2">Closed buyers</th><th className="text-right font-semibold py-2">Close %</th><th className="text-right font-semibold py-2">Written</th><th className="text-right font-semibold py-2">Collected</th><th className="text-right font-semibold py-2">Written / BU</th><th className="text-right font-semibold py-2">Collected / BU</th><th className="text-left font-semibold py-2">ABC</th><th className="text-left font-semibold py-2">Other stats</th></tr></thead><tbody>{rows.map((row) => <tr key={`${row.team}-${row.market}-${row.date}`} className="border-t border-border align-top"><td className="py-3 font-semibold">{row.market}</td><td className="py-3 text-muted-foreground">{row.date}</td><td className="py-3 text-right">{formatNumber(row.buyingUnits)}</td><td className="py-3 text-right">{fmtNumber(row.soldClosed)}</td><td className="py-3 text-right">{fmtPercentMaybe(row.soldClosed, row.buyingUnits)}</td><td className="py-3 text-right">{fmtMoney(row.totalWritten)}</td><td className="py-3 text-right">{fmtMoney(row.totalCollected)}</td><td className="py-3 text-right">{perBu(row.totalWritten, row.buyingUnits)}</td><td className="py-3 text-right">{perBu(row.totalCollected, row.buyingUnits)}</td><td className="py-3">{row.abcBreakdown ?? "N/A"}</td><td className="py-3 text-muted-foreground">{row.otherStats ?? "—"}</td></tr>)}<tr className="border-t-2 border-primary/30 bg-primary/5"><td className="py-3 font-bold">Total / weighted</td><td className="py-3 text-muted-foreground">{filter === "last6" ? "Last 6" : "YTD"}</td><td className="py-3 text-right font-bold">{formatNumber(total.buyingUnits)}</td><td className="py-3 text-right font-bold">{fmtNumber(total.closed)}</td><td className="py-3 text-right font-bold">{fmtPercentMaybe(total.closed, total.buyingUnits)}</td><td className="py-3 text-right font-bold">{fmtMoney(total.written)}</td><td className="py-3 text-right font-bold">{fmtMoney(total.collected)}</td><td className="py-3 text-right font-bold">{perBu(total.written, total.buyingUnits)}</td><td className="py-3 text-right font-bold">{perBu(total.collected, total.buyingUnits)}</td><td className="py-3 font-bold">N/A</td><td className="py-3 text-muted-foreground">ABC totals/mix source pending</td></tr></tbody></table></div>;
          })}
        </div>
      </SectionCard>
    </PageShell>
  );
};
export default Workshop;
