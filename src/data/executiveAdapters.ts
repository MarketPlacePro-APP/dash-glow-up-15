import type { SourceMeta } from '@/types';

const fetchedAt = '2026-05-05T08:29:55Z';

export type ExpoCount = {
  label: 'BU' | 'Guests' | 'UTL' | 'TLWB' | 'KeySpire' | 'Total';
  value: number;
  delta: number;
};

export type ActivePreviewMarket = {
  market: string;
  team: string;
  sessionsCompleted: number;
  totalSessions: number;
  registered: number;
  attendedCutoff: number;
  sales: number;
  previewShowRate: number;
  salesRate: number;
  status: 'green' | 'yellow' | 'red';
};

export type MarketingChannel = {
  channel: 'Facebook' | 'YouTube' | 'Google Search' | 'Total';
  regs: number;
  spend: number;
  cpr: number;
};

export type ActiveMarketingMarket = {
  market: string;
  starts: string;
  channels: MarketingChannel[];
};

export type MiddleEndSummary = {
  label: string;
  market: string;
  team: string;
  sold: number;
  attended: number;
  showRate: number;
  startDate: string;
};

export const executiveSources: SourceMeta[] = [
  {
    sourceKey: 'slack_expo_may_investor_expo_2026_04_29',
    sourceName: 'Slack #expo — May Investor Expo count post',
    sourceUrl: 'slack://channel/expo/post/2026-04-29T15:04-06:00',
    fetchedAt,
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'expo_count_slack_export',
    caveat: 'Counts use latest fetched #expo count post; deltas compare against prior fetched #expo count post on 2026-04-27.'
  },
  {
    sourceKey: 'slack_active_preview_atlanta_norfolk_2026_05_04',
    sourceName: 'Slack team channels — Atlanta/Norfolk active preview posts',
    sourceUrl: 'slack://channels/teamvogel,teamdent/latest-active-preview-posts',
    fetchedAt,
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'active_preview_slack_export',
    caveat: 'Aggregates completed/reported sessions only. Sales % uses 30-minute headcount/attended cutoff as denominator.'
  },
  {
    sourceKey: 'slack_eventstats_active_marketing_2026_05_04',
    sourceName: 'Slack #eventstats — active marketing posts',
    sourceUrl: 'slack://channel/eventstats/posts/2026-05-04',
    fetchedAt,
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'active_marketing_eventstats_export',
    caveat: 'Active marketing rows are pre-event registration/spend/CPR only; butt-in-seat counts intentionally unavailable until markets start.'
  },
  {
    sourceKey: 'slack_me_show_rates_2026_05_01',
    sourceName: 'Slack ME team channels — latest Friday ME show-rate check',
    sourceUrl: 'slack://channels/teamtony,teamshaw/latest-me-checkins',
    fetchedAt,
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'middle_end_show_rate_slack_export',
    caveat: 'Recent ME summary uses verified LA2 and Phoenix May 1 show-up checks; Fort Lauderdale pipeline count is source-pending until refreshed from latest ME pipeline source.'
  }
];

export const expoCounts: ExpoCount[] = [
  { label: 'BU', value: 131, delta: 6 },
  { label: 'Guests', value: 53, delta: 3 },
  { label: 'UTL', value: 42, delta: -1 },
  { label: 'TLWB', value: 88, delta: 6 },
  { label: 'KeySpire', value: 1, delta: 1 },
  { label: 'Total', value: 184, delta: 9 },
];

export const activePreviewMarkets: ActivePreviewMarket[] = [
  {
    market: 'Atlanta',
    team: 'Team Vogel',
    sessionsCompleted: 6,
    totalSessions: 10,
    registered: 1411,
    attendedCutoff: 162,
    sales: 46,
    previewShowRate: 162 / 1411,
    salesRate: 46 / 162,
    status: 'yellow'
  },
  {
    market: 'Norfolk',
    team: 'Team Dent',
    sessionsCompleted: 6,
    totalSessions: 10,
    registered: 1036,
    attendedCutoff: 132,
    sales: 40,
    previewShowRate: 132 / 1036,
    salesRate: 40 / 132,
    status: 'yellow'
  }
];

export const activeMarketingMarkets: ActiveMarketingMarket[] = [
  {
    market: 'Raleigh',
    starts: 'Wed May 27',
    channels: [
      { channel: 'Facebook', regs: 125, spend: 1353, cpr: 11 },
      { channel: 'YouTube', regs: 16, spend: 965, cpr: 60 },
      { channel: 'Google Search', regs: 0, spend: 28, cpr: 0 },
      { channel: 'Total', regs: 141, spend: 2347, cpr: 17 }
    ]
  },
  {
    market: 'Tampa',
    starts: 'Wed May 27',
    channels: [
      { channel: 'Facebook', regs: 161, spend: 1343, cpr: 8 },
      { channel: 'YouTube', regs: 23, spend: 995, cpr: 43 },
      { channel: 'Google Search', regs: 1, spend: 86, cpr: 86 },
      { channel: 'Total', regs: 185, spend: 2424, cpr: 13 }
    ]
  },
  {
    market: 'West Palm Beach',
    starts: 'Sat May 16',
    channels: [
      { channel: 'Facebook', regs: 681, spend: 12952, cpr: 19 },
      { channel: 'YouTube', regs: 155, spend: 7190, cpr: 46 },
      { channel: 'Google Search', regs: 11, spend: 1102, cpr: 100 },
      { channel: 'Total', regs: 847, spend: 21244, cpr: 25 }
    ]
  }
];

export const middleEndSummary: MiddleEndSummary[] = [
  { label: 'Recent ME', market: 'LA2', team: 'Team Tony', sold: 38, attended: 30, showRate: 30 / 38, startDate: '2026-05-01' },
  { label: 'Recent ME', market: 'Phoenix', team: 'Team Shaw / Megan', sold: 29, attended: 23, showRate: 23 / 29, startDate: '2026-05-01' },
];

export const upcomingMePipeline = {
  market: 'Fort Lauderdale',
  expected: 140,
  status: 'source pending',
  note: 'Pipeline count requested in walkthrough; keep marked source pending until refreshed from latest ME pipeline source.'
};
