export type TrustLevel = 'final' | 'operational' | 'tracker' | 'analytic' | 'reference';

export interface SourceMeta {
  sourceKey: string;
  sourceName: string;
  sourceUrl: string;
  fetchedAt: string;
  trustLevel: TrustLevel;
  sampleData: boolean;
  sourceRole?: string;
  caveat?: string;
}

export interface FinalMarketRecord extends SourceMeta {
  market: string;
  date: string;
  team: string;
  finalRegistrations: number;
  finalAttendees: number;
  finalDeals: number;
  showRate: number;
  futures?: number;
  penders?: number;
}

export interface MarketTrackerRecord extends SourceMeta {
  market: string;
  date: string;
  totalRegistered: number;
  totalAttended: number;
  totalBuyers: number;
  spend: number;
  written: number;
  collected: number;
  collected90Day: number;
  channels: Array<{
    channel: string;
    registered: number;
    attended: number;
  }>;
}

export interface SessionRecord extends SourceMeta {
  market: string;
  date: string;
  sessionNumber: number;
  location: string;
  registration: number;
  attended: number;
  deals: number;
  showRate: number;
  written: number;
  collected: number;
  spend: number;
  cpa: number;
  dpl: number;
}

export interface ScheduleRecord extends SourceMeta {
  id: string;
  market: string;
  route: string;
  team: string;
  teamKey: string;
  weekOf: string;
  startDate: string;
  endDate: string;
  location: string;
  state: 'active' | 'tentative' | 'historical' | 'upcoming' | 'reference';
  owner: string;
  eventType: 'front_end_preview' | 'middle_end_workshop' | 'expo' | 'off' | 'planning' | 'unknown';
  area?: string;
  city?: string;
  venue?: string;
  address?: string;
  times?: string;
  parking?: string;
  ballroom?: string;
  locationCode?: string;
  hotelStatus?: string;
  onSiteContact?: string;
  sourceSheet: string;
  sourceRow: number;
  sourceTabRole: 'operational_schedule' | 'calendar_rollup' | 'route_detail' | 'reference';
  notes?: string;
}

export interface ScheduleRouteBlock extends SourceMeta {
  id: string;
  market: string;
  route: string;
  team: string;
  teamKey: string;
  status: 'active' | 'tentative' | 'historical' | 'upcoming' | 'reference';
  startDate: string;
  endDate: string;
  eventCount: number;
  areas: string[];
  venues: string[];
  sourceSheet: string;
  sourceRows: number[];
}

export interface TeamKpiRecord extends SourceMeta {
  periodLabel: string;
  periodType: 'prior_week' | 'ytd';
  team: string;
  leads: number;
  written: number;
  collected: number;
  dpl: number;
  cancelCount: number;
  cancelDollars: number;
  cancelRate: number;
  refundCount: number;
  refundDollars: number;
  refundRate: number;
  bouncedAchCount: number;
  bouncedAchDollars: number;
  bouncedAchRate: number;
  recollectedDollars: number;
  netRealizedCash: number;
}

export interface SegMetricsRecord extends SourceMeta {
  dateRange: string;
  dimension: 'campaign' | 'account' | 'ad';
  name: string;
  spend: number;
  leads: number;
  customers: number;
  revenue: number;
  cpl: number;
  cac: number;
}

export interface SpeakerBenchmarkRecord extends SourceMeta {
  speaker: string;
  grossMonetization: number;
  balancedScore: number;
  buyerTierA: number;
  buyerTierB: number;
  buyerTierC: number;
  collectedQuality: number;
}

export interface MarketOpsRecord extends SourceMeta {
  mode: 'preview' | 'workshop';
  team: string;
  market: string;
  date?: string;
  status?: 'active' | 'final' | 'last_completed' | 'pending';
  registrations?: number;
  sold: number;
  attended: number;
  deals: number;
  confirmedMeBuyers?: number;
  meAttended?: number;
  spend?: number;
  costPerRegistration?: number;
  bisCost?: number;
  cpa?: number;
  showUpRate: number;
  notes?: string;
}

export interface DashboardDataset {
  finals: FinalMarketRecord[];
  tracker: MarketTrackerRecord[];
  sessions: SessionRecord[];
  schedule: ScheduleRecord[];
  scheduleRouteBlocks: ScheduleRouteBlock[];
  legacySchedule: ScheduleRecord[];
  teamKpis: TeamKpiRecord[];
  segMetrics: SegMetricsRecord[];
  speakerBenchmarks: SpeakerBenchmarkRecord[];
  marketOps: MarketOpsRecord[];
}
