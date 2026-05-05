import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { DashboardDataset, MarketOpsRecord, SourceMeta } from '@/types';
import { loadDashboardData } from './dashboardStore';
import { expoStrip } from './expoStrip';
import { executiveSources, expoCounts, activePreviewMarkets, activeMarketingMarkets, middleEndSummary, upcomingMePipeline } from './executiveAdapters';

const DashboardDataContext = createContext<DashboardDataset | null>(null);

export function DashboardDataProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<DashboardDataset | null>(null);

  useEffect(() => {
    loadDashboardData().then(setData);
  }, []);

  if (!data) {
    return (
      <div className="min-h-screen bg-background text-foreground grid place-items-center">
        <div className="glass border border-border rounded-2xl p-6 text-sm text-muted-foreground">Loading TLWB KPI data…</div>
      </div>
    );
  }

  return <DashboardDataContext.Provider value={data}>{children}</DashboardDataContext.Provider>;
}

export function useDashboardData() {
  const data = useContext(DashboardDataContext);
  if (!data) throw new Error('useDashboardData must be used within DashboardDataProvider');
  return data;
}

export function latestSource(data: DashboardDataset): SourceMeta | undefined {
  return mostRecentSource(sourceRows(data));
}

export function mostRecentSource(sources: SourceMeta[]) {
  return [...sources].sort((a, b) => Date.parse(b.fetchedAt || '') - Date.parse(a.fetchedAt || ''))[0];
}

export function overallSourceMode(data: DashboardDataset): 'live' | 'export' | 'static' {
  const sources = sourceRows(data);
  if (sources.some((s) => s.sourceRole?.includes('live'))) return 'live';
  if (sources.some((s) => s.sourceUrl?.includes('google_exports') || s.sourceRole?.includes('export'))) return 'export';
  return 'static';
}

export function sourceModeFor(source: SourceMeta): 'live' | 'export' | 'static' {
  if (source.sourceRole?.includes('live')) return 'live';
  if (source.sourceUrl?.includes('google_exports') || source.sourceRole?.includes('export')) return 'export';
  return 'static';
}

export function sourceStatus(source: SourceMeta, now = new Date()) {
  const fetched = Date.parse(source.fetchedAt || '');
  if (!Number.isFinite(fetched)) return 'unknown';
  const ageDays = (now.getTime() - fetched) / 86_400_000;
  if (source.sampleData) return 'placeholder';
  if (ageDays <= 1) return 'current';
  if (ageDays <= 7) return 'watch';
  return 'stale';
}

export function exportDateLabel(source: SourceMeta) {
  const match = source.sourceUrl?.match(/(20\d{2}-\d{2}-\d{2})/);
  return match?.[1] ?? source.fetchedAt?.slice(0, 10) ?? 'unknown';
}

export function sum<T>(items: T[], pick: (item: T) => number | undefined) {
  return items.reduce((total, item) => total + (pick(item) ?? 0), 0);
}

export function getPreviewOps(data: DashboardDataset) {
  return data.marketOps.filter((item) => item.mode === 'preview');
}

export function getWorkshopOps(data: DashboardDataset) {
  return data.marketOps.filter((item) => item.mode === 'workshop');
}

export function activePreviewOps(data: DashboardDataset) {
  const ops = getPreviewOps(data).filter((item) => item.status === 'active');
  return ops.length ? ops : getPreviewOps(data).slice(0, 4);
}

export function latestCompletedPreviewOps(data: DashboardDataset) {
  const rows = getPreviewOps(data).filter((item) => item.status === 'last_completed' || item.status === 'final');
  return rows.length ? rows.slice(0, 5) : getPreviewOps(data).slice(0, 5);
}

export function sourceRows(data: DashboardDataset) {
  const sources = new Map<string, SourceMeta & { rowCount: number }>();
  const ingest = (source: SourceMeta | undefined) => {
    if (!source) return;
    const existing = sources.get(source.sourceKey);
    sources.set(source.sourceKey, { ...source, rowCount: (existing?.rowCount ?? 0) + 1 });
  };
  data.finals.forEach(ingest);
  data.tracker.forEach(ingest);
  data.sessions.forEach(ingest);
  data.schedule.forEach(ingest);
  data.teamKpis.forEach(ingest);
  data.marketOps.forEach(ingest);
  ingest(expoStrip.source);
  executiveSources.forEach(ingest);
  return Array.from(sources.values()).sort((a, b) => a.sourceName.localeCompare(b.sourceName));
}

export function useExecutiveMetrics() {
  const data = useDashboardData();
  return useMemo(() => {
    const active = activePreviewOps(data).slice(0, 4);
    const preview = active.length ? active : data.marketOps.filter((item) => item.mode === 'preview').slice(0, 4);
    const workshops = getWorkshopOps(data).slice(0, 4);
    const registered = sum(preview, (item) => item.registrations);
    const attended = sum(preview, (item) => item.attended);
    const sold = sum(preview, (item) => item.sold || item.deals);
    const spend = sum(preview, (item) => item.spend);
    const workshopSold = sum(workshops, (item) => item.confirmedMeBuyers ?? item.sold);
    const workshopShowed = sum(workshops, (item) => item.meAttended ?? item.attended);
    return { data, active, preview, workshops, registered, attended, sold, spend, showRate: registered ? attended / registered : 0, salesRate: attended ? sold / attended : 0, workshopSold, workshopShowed, meShowRate: workshopSold ? workshopShowed / workshopSold : 0, lastRefreshed: latestSource(data)?.fetchedAt ?? 'unknown', sourceMode: overallSourceMode(data), expoStrip, expoCounts, activePreviewMarkets, activeMarketingMarkets, middleEndSummary, upcomingMePipeline };
  }, [data]);
}

export function marketDateLabel(item: MarketOpsRecord) {
  if (!item.date) return 'date pending';
  return new Date(`${item.date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
