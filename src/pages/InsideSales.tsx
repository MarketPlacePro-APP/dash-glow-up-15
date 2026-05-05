import { useState } from "react";
import { Activity, ChevronDown, DollarSign, Target, TrendingUp } from "lucide-react";
import { PageShell, SectionCard, Stat } from "@/components/dashboard/PageShell";
import { insideSalesRepRows, insideSalesSourceCategories, speakerCollectionRows } from "@/data/tlwbPageAdapters";
import { formatCurrency, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

const toneClass: Record<string, string> = { primary: "text-primary bg-primary/10", success: "text-success bg-success/10", warning: "text-warning bg-warning/10" };
const fmtMoney = (value: number | null) => value === null ? "Source pending" : formatCurrency(value);
const fmtNum = (value: number | null) => value === null ? "Source pending" : formatNumber(value);

const InsideSales = () => {
  const [openSpeaker, setOpenSpeaker] = useState<string | null>(speakerCollectionRows[0]?.speaker ?? null);
  const summary = [
    { label: "YTD Leads", value: "Source pending", icon: Target, tone: "primary" },
    { label: "YTD Revenue", value: "Source pending", icon: DollarSign, tone: "primary" },
    { label: "YTD Collections", value: "Source pending", icon: TrendingUp, tone: "success" },
    { label: "DPL", value: "Source pending", icon: Activity, tone: "warning" },
  ];

  return (
    <PageShell eyebrow="INSIDE SALES" title="Inside Sales DPL & Collections" description="Focused on Inside Sales lead-source DPL, rep ranking, and pending collections. Source dashboard link is still needed before numbers are populated.">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
        {summary.map((s) => { const Icon = s.icon; return <div key={s.label} className="glass border border-border rounded-xl p-4"><div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", toneClass[s.tone])}><Icon className="h-4 w-4" /></div><p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{s.label}</p><p className="text-xl font-bold tracking-tight mt-0.5">{s.value}</p></div>; })}
      </section>

      <SectionCard eyebrow="Source Status" title="Inside Sales source needed" subtitle="Likely source: Lindsey’s UTL app / performance dashboard or child spreadsheets behind it.">
        <div className="rounded-xl border border-warning/30 bg-warning/10 p-5 text-sm text-muted-foreground">
          <p className="font-semibold text-foreground mb-2">No sourced Inside Sales DPL dataset is connected in the current dashboard model.</p>
          <p>To avoid fabricating DPL, collections, or pending speaker balances, this page is wired with the required structure and explicit source-pending fields. Once Troy confirms the UTL performance dashboard link / export, these tables can hydrate from that source.</p>
        </div>
      </SectionCard>

      <SectionCard eyebrow="Lead Sources" title="YTD performance by lead/source category" subtitle="All categories requested by Troy are present; unavailable metrics are marked source pending.">
        <div className="overflow-x-auto -mx-2"><table className="w-full text-sm min-w-[920px]"><thead><tr className="text-[10px] uppercase tracking-wide text-muted-foreground"><th className="text-left font-semibold px-2 py-2">Source</th><th className="text-right font-semibold px-2 py-2">Leads</th><th className="text-right font-semibold px-2 py-2">Revenue</th><th className="text-right font-semibold px-2 py-2">Pending collections</th><th className="text-right font-semibold px-2 py-2">YTD collections</th><th className="text-right font-semibold px-2 py-2">6-week YTD</th><th className="text-right font-semibold px-2 py-2">10-week YTD</th></tr></thead><tbody>{insideSalesSourceCategories.map((row) => <tr key={row.source} className="border-t border-border"><td className="px-2 py-3 font-semibold">{row.source}</td><td className="px-2 py-3 text-right">{fmtNum(row.leads)}</td><td className="px-2 py-3 text-right">{fmtMoney(row.revenue)}</td><td className="px-2 py-3 text-right">{fmtMoney(row.pendingCollections)}</td><td className="px-2 py-3 text-right">{fmtMoney(row.ytdCollections)}</td><td className="px-2 py-3 text-right">{fmtMoney(row.sixWeekYtd)}</td><td className="px-2 py-3 text-right">{fmtMoney(row.tenWeekYtd)}</td></tr>)}</tbody></table></div>
      </SectionCard>

      <SectionCard eyebrow="Rep Ranking" title="DPL ranked by rep" subtitle="Designed for rep-level leads, revenue, DPL, collected amount, and collected DPL once the source export is connected.">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {insideSalesRepRows.map((rep) => <div key={rep.rep} className="rounded-xl border border-border bg-card/60 p-5"><div className="flex items-center justify-between gap-3 mb-4"><h4 className="font-bold">{rep.rep}</h4><span className="text-[10px] rounded-full bg-warning/15 text-warning px-2 py-1 font-semibold">source pending</span></div><div className="grid grid-cols-2 lg:grid-cols-5 gap-3"><Stat label="Leads" value={fmtNum(rep.leads)} /><Stat label="Revenue" value={fmtMoney(rep.revenue)} /><Stat label="Total DPL" value={fmtMoney(rep.dpl)} /><Stat label="Collected" value={fmtMoney(rep.collected)} /><Stat label="Collected DPL" value={fmtMoney(rep.collectedDpl)} /></div><p className="mt-3 text-xs text-muted-foreground">{rep.source}</p></div>)}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Speaker Collections" title="Pending and completed collections by speaker" subtitle="Expandable speaker/source grouping for collections in, collections out, pending amount, and related DPL/collection metrics.">
        <div className="space-y-3">
          {speakerCollectionRows.map((row) => {
            const open = openSpeaker === row.speaker;
            return <div key={row.speaker} className="rounded-xl border border-border bg-card/50"><button type="button" onClick={() => setOpenSpeaker(open ? null : row.speaker)} className="w-full flex items-center justify-between gap-3 p-4 text-left"><div><p className="font-semibold">{row.speaker}</p><p className="text-xs text-muted-foreground">Pending/outstanding: {fmtMoney(row.pendingOutstanding)}</p></div><ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} /></button>{open ? <div className="border-t border-border p-4 grid grid-cols-1 md:grid-cols-4 gap-3"><Stat label="Into collections" value={fmtMoney(row.amountIntoCollections)} /><Stat label="Collections out" value={fmtMoney(row.collectionsOut)} /><Stat label="Pending" value={fmtMoney(row.pendingOutstanding)} /><Stat label="Metric" value={row.dplOrCollectionMetric ?? "Source pending"} /></div> : null}</div>;
          })}
        </div>
      </SectionCard>
    </PageShell>
  );
};
export default InsideSales;
