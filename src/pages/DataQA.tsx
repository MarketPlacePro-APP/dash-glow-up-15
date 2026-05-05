import { AlertTriangle, Database, RefreshCw, ShieldCheck } from "lucide-react";
import { PageShell, SectionCard } from "@/components/dashboard/PageShell";
import { exportDateLabel, mostRecentSource, sourceRows, useDashboardData } from "@/data/DashboardDataProvider";
import { cn } from "@/lib/utils";

type SourceType = "live" | "export" | "static" | "manual" | "Slack" | "Google Sheet";
type Health = "current" | "watch" | "stale" | "unavailable" | "source pending";

type OperationalSource = {
  key: string;
  sourceName: string;
  sourceType: SourceType;
  sourceDate: string;
  fetchedAt: string;
  lastSuccessfulRefresh: string;
  rowsLoaded: number | null;
  status: Health;
  pages: string[];
  notes: string;
};

const typeChip: Record<SourceType, string> = {
  live: "bg-success/15 text-success",
  export: "bg-primary/15 text-primary",
  static: "bg-muted text-muted-foreground",
  manual: "bg-warning/15 text-warning",
  Slack: "bg-purple-500/15 text-purple-300",
  "Google Sheet": "bg-emerald-500/15 text-emerald-300",
};

const statusChip: Record<Health, string> = {
  current: "bg-success/15 text-success",
  watch: "bg-warning/15 text-warning",
  stale: "bg-destructive/15 text-destructive",
  unavailable: "bg-destructive/15 text-destructive",
  "source pending": "bg-warning/15 text-warning",
};

const classifyStatus = (fetchedAt: string, sourceDate: string, unavailable = false): Health => {
  if (unavailable) return "source pending";
  const fetched = Date.parse(fetchedAt);
  if (!Number.isFinite(fetched)) return "unavailable";
  const fetchedAgeDays = (Date.now() - fetched) / 86_400_000;
  const source = Date.parse(sourceDate);
  const sourceAgeDays = Number.isFinite(source) ? (Date.now() - source) / 86_400_000 : fetchedAgeDays;
  if (fetchedAgeDays <= 1 && sourceAgeDays <= 2) return "current";
  if (fetchedAgeDays <= 7 && sourceAgeDays <= 10) return "watch";
  return "stale";
};

const pageList = (pages: string[]) => pages.join(" · ");

const DataQA = () => {
  const data = useDashboardData();
  const rawSources = sourceRows(data);
  const latest = mostRecentSource(rawSources);
  const countByKey = new Map(rawSources.map((source) => [source.sourceKey, source.rowCount]));
  const sourceByKey = new Map(rawSources.map((source) => [source.sourceKey, source]));
  const numbers = sourceByKey.get("numbers_per_session_adapter");
  const schedule = sourceByKey.get("schedule_adapter");
  const tracker = sourceByKey.get("market_comparisons_adapter");
  const teamKpis = sourceByKey.get("ws_sales_tracker_adapter");

  const sources: OperationalSource[] = [
    {
      key: "slack_eventstats_active_marketing_2026_05_04",
      sourceName: "Event Stats — active marketing posts",
      sourceType: "Slack",
      sourceDate: "2026-05-04",
      fetchedAt: "2026-05-05T08:29:55Z",
      lastSuccessfulRefresh: "2026-05-05T08:29:55Z",
      rowsLoaded: countByKey.get("slack_eventstats_active_marketing_2026_05_04") ?? 1,
      status: classifyStatus("2026-05-05T08:29:55Z", "2026-05-04"),
      pages: ["Executive", "Marketing"],
      notes: "Raleigh, Tampa, and West Palm Beach channel regs/spend/CPR from latest fetched #eventstats posts. Not live; refresh job must fetch newer posts before values are advanced.",
    },
    {
      key: "numbers_per_session_adapter",
      sourceName: "Numbers Per Session",
      sourceType: "Google Sheet",
      sourceDate: exportDateLabel(numbers ?? { sourceUrl: "", fetchedAt: "", sourceKey: "", sourceName: "", trustLevel: "operational", sampleData: false }),
      fetchedAt: numbers?.fetchedAt ?? "unavailable",
      lastSuccessfulRefresh: numbers?.fetchedAt ?? "unavailable",
      rowsLoaded: countByKey.get("numbers_per_session_adapter") ?? null,
      status: classifyStatus(numbers?.fetchedAt ?? "", numbers?.fetchedAt ?? "", !numbers),
      pages: ["Preview", "Marketing", "Data QA"],
      notes: "Session-level and rollup export used for historical market/session context where final Slack posts are not more specific.",
    },
    {
      key: "slack_active_preview_atlanta_norfolk_2026_05_04",
      sourceName: "Slack finals/team channels — active preview sessions",
      sourceType: "Slack",
      sourceDate: "2026-05-04",
      fetchedAt: "2026-05-05T08:29:55Z",
      lastSuccessfulRefresh: "2026-05-05T08:29:55Z",
      rowsLoaded: countByKey.get("slack_active_preview_atlanta_norfolk_2026_05_04") ?? 1,
      status: classifyStatus("2026-05-05T08:29:55Z", "2026-05-04"),
      pages: ["Executive", "Preview"],
      notes: "Atlanta/Team Vogel and Norfolk/Team Dent session posts. Sales % uses on-time 30-minute headcount denominator.",
    },
    {
      key: "schedule_adapter",
      sourceName: "TLWB/MO Schedule sheet",
      sourceType: "Google Sheet",
      sourceDate: exportDateLabel(schedule ?? { sourceUrl: "", fetchedAt: "", sourceKey: "", sourceName: "", trustLevel: "operational", sampleData: false }),
      fetchedAt: schedule?.fetchedAt ?? "unavailable",
      lastSuccessfulRefresh: schedule?.fetchedAt ?? "unavailable",
      rowsLoaded: (countByKey.get("schedule_adapter") ?? 0) + data.scheduleRouteBlocks.length,
      status: classifyStatus(schedule?.fetchedAt ?? "", schedule?.fetchedAt ?? "", !schedule),
      pages: ["Executive", "Schedule"],
      notes: "Preview route calendar source. Supplemental ME/Expo items are labeled separately because they were missing from the FE route export.",
    },
    {
      key: "market_comparisons_adapter",
      sourceName: "Lindsey hub / child sheets — Market Comparisons",
      sourceType: "export",
      sourceDate: exportDateLabel(tracker ?? { sourceUrl: "", fetchedAt: "", sourceKey: "", sourceName: "", trustLevel: "analytic", sampleData: false }),
      fetchedAt: tracker?.fetchedAt ?? "unavailable",
      lastSuccessfulRefresh: tracker?.fetchedAt ?? "unavailable",
      rowsLoaded: countByKey.get("market_comparisons_adapter") ?? null,
      status: classifyStatus(tracker?.fetchedAt ?? "", tracker?.fetchedAt ?? "", !tracker),
      pages: ["Data QA", "legacy diagnostics"],
      notes: "Diagnostic/forecast source only. Do not use to override Slack finals or current session posts without reconciliation.",
    },
    {
      key: "inside_sales_performance_dashboard",
      sourceName: "Inside Sales performance dashboard / child sheets",
      sourceType: "live",
      sourceDate: "source pending",
      fetchedAt: "unavailable",
      lastSuccessfulRefresh: "unavailable",
      rowsLoaded: null,
      status: "source pending",
      pages: ["Inside Sales"],
      notes: "Needed for rep-ranked DPL, lead-source categories, 6-week/10-week YTD, and speaker pending collections. Current page intentionally shows Source pending/N/A rather than fabricated values.",
    },
    {
      key: "workshop_me_final_reports",
      sourceName: "Workshop/ME final reports",
      sourceType: "manual",
      sourceDate: "source pending",
      fetchedAt: "unavailable",
      lastSuccessfulRefresh: "unavailable",
      rowsLoaded: null,
      status: "source pending",
      pages: ["Workshop / ME"],
      notes: "Required for written, collected, per-BU, ABC breakdown, and final close % fields. Show-up check-ins are present; final financial/ABC metrics remain N/A.",
    },
    {
      key: "slack_me_show_rates_2026_05_01",
      sourceName: "Slack ME team check-ins",
      sourceType: "Slack",
      sourceDate: "2026-05-01",
      fetchedAt: "2026-05-05T08:29:55Z",
      lastSuccessfulRefresh: "2026-05-05T08:29:55Z",
      rowsLoaded: countByKey.get("slack_me_show_rates_2026_05_01") ?? 1,
      status: classifyStatus("2026-05-05T08:29:55Z", "2026-05-01"),
      pages: ["Executive", "Workshop / ME", "Schedule"],
      notes: "LA2/Team Tony and Phoenix/Team Shaw ME show-up checks. This does not include written/collected/ABC final report data.",
    },
    {
      key: "slack_expo_may_investor_expo_2026_04_29",
      sourceName: "Expo strip source — Slack #expo May Investor Expo count",
      sourceType: "Slack",
      sourceDate: "2026-04-29T15:04:00-06:00",
      fetchedAt: "2026-05-05T07:26:09Z",
      lastSuccessfulRefresh: "2026-05-05T07:26:09Z",
      rowsLoaded: countByKey.get("slack_expo_may_investor_expo_2026_04_29") ?? 1,
      status: classifyStatus("2026-05-05T07:26:09Z", "2026-04-29T15:04:00-06:00"),
      pages: ["Executive", "Schedule", "Data QA"],
      notes: "Static Slack export until a newer #expo count is fetched. Deltas compare latest fetched May count with prior fetched count.",
    },
    {
      key: "ws_sales_tracker_adapter",
      sourceName: "Lindsey hub / child sheets — WS Sales Tracker",
      sourceType: "export",
      sourceDate: exportDateLabel(teamKpis ?? { sourceUrl: "", fetchedAt: "", sourceKey: "", sourceName: "", trustLevel: "tracker", sampleData: false }),
      fetchedAt: teamKpis?.fetchedAt ?? "unavailable",
      lastSuccessfulRefresh: teamKpis?.fetchedAt ?? "unavailable",
      rowsLoaded: countByKey.get("ws_sales_tracker_adapter") ?? null,
      status: classifyStatus(teamKpis?.fetchedAt ?? "", teamKpis?.fetchedAt ?? "", !teamKpis),
      pages: ["Data QA", "Inside Sales source reference"],
      notes: "Available WS tracker records are not a substitute for the requested Inside Sales DPL/source/collections dashboard.",
    },
  ];

  const connected = sources.filter((s) => !["unavailable", "source pending"].includes(s.status)).length;
  const needsReview = sources.filter((s) => s.status !== "current").length;
  const totalRows = sources.reduce((n, s) => n + (s.rowsLoaded ?? 0), 0);

  return (
    <PageShell eyebrow="DATA QA" title="Source Freshness & Health" description="Operational source ledger with real timestamps, source dates, page usage, and unavailable/stale status. No relative freshness labels.">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-up">
        <Tile icon={ShieldCheck} label="Connected Sources" value={`${connected} / ${sources.length}`} tone="success" />
        <Tile icon={AlertTriangle} label="Needs Review" value={`${needsReview}`} tone="warning" />
        <Tile icon={RefreshCw} label="Latest Refresh" value={latest?.fetchedAt?.slice(0, 10) ?? "pending"} tone="primary" />
        <Tile icon={Database} label="Rows Loaded" value={totalRows.toLocaleString()} tone="primary" />
      </section>

      <SectionCard eyebrow="Operational Source Ledger" title="Required sources and freshness">
        <div className="overflow-x-auto -mx-2">
          <table className="w-full text-sm min-w-[1220px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wide text-muted-foreground">
                <th className="text-left font-semibold px-2 py-2">Source</th>
                <th className="text-left font-semibold px-2 py-2">Type</th>
                <th className="text-left font-semibold px-2 py-2">Fetched timestamp</th>
                <th className="text-left font-semibold px-2 py-2">Source / export date</th>
                <th className="text-right font-semibold px-2 py-2">Rows loaded</th>
                <th className="text-left font-semibold px-2 py-2">Last successful refresh</th>
                <th className="text-left font-semibold px-2 py-2">Status</th>
                <th className="text-left font-semibold px-2 py-2">Pages using source</th>
                <th className="text-left font-semibold px-2 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.key} className="border-t border-border align-top">
                  <td className="px-2 py-3 font-semibold">{source.sourceName}</td>
                  <td className="px-2 py-3"><span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold", typeChip[source.sourceType])}>{source.sourceType}</span></td>
                  <td className="px-2 py-3">{source.fetchedAt}</td>
                  <td className="px-2 py-3">{source.sourceDate}</td>
                  <td className="px-2 py-3 text-right">{source.rowsLoaded === null ? "N/A" : source.rowsLoaded.toLocaleString()}</td>
                  <td className="px-2 py-3">{source.lastSuccessfulRefresh}</td>
                  <td className="px-2 py-3"><span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold", statusChip[source.status])}>{source.status}</span></td>
                  <td className="px-2 py-3">{pageList(source.pages)}</td>
                  <td className="px-2 py-3 text-muted-foreground">{source.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </PageShell>
  );
};

const Tile = ({ icon: Icon, label, value, tone }: { icon: typeof ShieldCheck; label: string; value: string; tone: "primary" | "success" | "warning" }) => {
  const tones: Record<string, string> = { primary: "text-primary bg-primary/10", success: "text-success bg-success/10", warning: "text-warning bg-warning/10" };
  return <div className="glass border border-border rounded-xl p-4"><div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", tones[tone])}><Icon className="h-4 w-4" /></div><p className="mt-3 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{label}</p><p className="text-2xl font-bold tracking-tight mt-0.5">{value}</p></div>;
};
export default DataQA;
