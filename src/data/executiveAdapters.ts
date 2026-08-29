import type { SourceMeta } from '@/types';

const fetchedAt = '2026-06-06T17:20:00Z';

export type ExpoCount = {
  label: 'BU' | 'Guests' | 'UTL' | 'TLWB' | 'KeySpire' | 'Total';
  value: number | null;
  delta: number | null;
};

export type ActivePreviewMarket = {
  market: string;
  team: string;
  sessionsCompleted: number | null;
  totalSessions: number | null;
  registered: number;
  attendedCutoff: number;
  sales: number;
  routeDeals?: number;
  futures?: number;
  previewShowRate: number;
  salesRate: number;
  status: 'green' | 'yellow' | 'red';
  sourceState?: 'active_session' | 'session_detail' | 'final_route_totals' | 'pending_source';
  startDate?: string;
  latestSessionDate?: string;
  sourcePostedAt?: string;
  sourceNote?: string;
};

export type MarketingChannel = {
  channel: 'Facebook' | 'YouTube' | 'Google Search' | 'Total';
  regs: number;
  spend: number;
  cpr: number;
};

export type ActiveMarketingMarket = {
  market: string;
  startDate?: string;
  starts: string;
  channels: MarketingChannel[];
};

export type MiddleEndSummary = {
  label: string;
  period: 'Last week' | 'Two weeks prior';
  market: string;
  team: string;
  sold: number;
  attended: number;
  showRate: number;
  startDate: string;
  workshopSales?: number;
  sourceNote?: string;
};

export type UpcomingMePipelineMarket = {
  market: string;
  previewTeam: string;
  middleEndTeam: string;
  startDate: string | null;
  endDate?: string | null;
  previewSold: number | null;
  projectedBuyingUnits: number | null;
  middleEndSold: number | null;
  source: string;
  sourcePostedAt?: string;
};

export const executiveSources: SourceMeta[] = [
  {
    sourceKey: 'slack_expo_current_2026_08_29',
    sourceName: 'Slack #expo — current Investor Expo count',
    sourceUrl: 'slack://channel/expo/posts/2026-07-22T14:55:54.888579-06:00',
    fetchedAt: '2026-08-29T06:04:55.955799-06:00',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'expo_strip_current_count',
    caveat: 'August Investor Expo current count parsed from live #expo: 129 BU, 72 guests, total 201.'
  },
  {
    sourceKey: 'slack_active_preview_2026_08_29',
    sourceName: 'Slack preview team channels — latest final route reports',
    sourceUrl: 'slack://channels/teamwayne,teamdent,teamwyman,teamvogel,teammillar/latest-final-route-reports',
    fetchedAt: '2026-08-29T06:04:55.955799-06:00',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'active_preview_slack_export',
    caveat: 'Latest final route reports are parsed from visible preview team channels. Cron fails if fewer than three final market reports parse.'
  },
  {
    sourceKey: 'slack_eventstats_active_marketing_2026_08_29',
    sourceName: 'Slack #eventstats — active marketing posts',
    sourceUrl: 'slack://channel/eventstats/latest-active-workshop-posts',
    fetchedAt: '2026-08-29T06:04:55.955799-06:00',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'active_marketing_eventstats_export',
    caveat: 'Active marketing cards are rebuilt from the latest unique #eventstats workshop posts before deploy.'
  },
  {
    sourceKey: 'slack_me_finals_2026_08_29',
    sourceName: 'Slack ME team channels — current workshop finals',
    sourceUrl: 'slack://channels/teamtony,teamshaw,teamdrecksel,teamnick/latest-workshop-finals',
    fetchedAt: '2026-08-29T06:04:55.955799-06:00',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'middle_end_show_rate_slack_export',
    caveat: 'Current Workshop/ME rows are rebuilt from latest visible final workshop posts before deploy.'
  }
];

export const expoCounts: ExpoCount[] = [
  { label: 'BU', value: 129, delta: null },
  { label: 'Guests', value: 72, delta: null },
  { label: 'UTL', value: 7, delta: null },
  { label: 'TLWB', value: 95, delta: null },
  { label: 'KeySpire', value: 0, delta: null },
  { label: 'Total', value: 201, delta: null }
];

export const activePreviewMarkets: ActivePreviewMarket[] = [
  {
    market: 'Atlanta',
    team: 'Team Wayne/Gray / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 1347,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-08-29',
    sourcePostedAt: '2026-08-28T11:33:34.204209-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:33:34.204209-06:00: 1347 total registrations; route starts Saturday August 29th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'White Plains',
    team: 'Team Vogel/Cord / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 1070,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-08-29',
    sourcePostedAt: '2026-08-28T11:35:06.234709-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:35:06.234709-06:00: 1070 total registrations; route starts Saturday August 29th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Baltimore',
    team: 'Team Wayne/Gray / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 706,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-09',
    sourcePostedAt: '2026-08-28T11:39:52.876389-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:39:52.876389-06:00: 706 total registrations; route starts Wednesday September 9th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Newark',
    team: 'Team Vogel/Cord / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 659,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-09',
    sourcePostedAt: '2026-08-28T11:36:45.124459-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:36:45.124459-06:00: 659 total registrations; route starts Wednesday September 9th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Richmond',
    team: 'Team Vogel/Cord / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 463,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-09',
    sourcePostedAt: '2026-08-28T11:38:16.302899-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:38:16.302899-06:00: 463 total registrations; route starts Wednesday September 9th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Norfolk',
    team: 'Team Vogel/Cord / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 326,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-13',
    sourcePostedAt: '2026-08-28T11:44:24.482249-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:44:24.482249-06:00: 326 total registrations; route starts Sunday September 13th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Philadelphia',
    team: 'Team Vogel/Cord / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 429,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-13',
    sourcePostedAt: '2026-08-28T11:41:36.630319-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:41:36.630319-06:00: 429 total registrations; route starts Sunday September 13th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'Washington DC',
    team: 'Team Wayne/Gray / #eventstats',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 275,
    attendedCutoff: 0,
    sales: 0,
    routeDeals: 0,
    previewShowRate: 0,
    salesRate: 0,
    status: 'yellow',
    sourceState: 'pending_source',
    startDate: '2026-09-13',
    sourcePostedAt: '2026-08-28T11:45:53.860799-06:00',
    sourceNote: 'Pre-event #eventstats registration and spend source at 2026-08-28T11:45:53.860799-06:00: 275 total registrations; route starts Sunday September 13th. Slack floor/session results are pending until the first Preview session posts.'
  },
  {
    market: 'St. Louis, MO',
    team: 'Team Wayne · Speaker Nick / #teamwayne',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 1097,
    attendedCutoff: 142,
    sales: 46,
    routeDeals: 48,
    previewShowRate: 142 / 1097,
    salesRate: 48 / 142,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-22',
    latestSessionDate: '2026-08-26',
    sourcePostedAt: '2026-08-26T20:10:02.069079-06:00',
    sourceNote: 'Final route report from #teamwayne, labeled Team Wayne, at 2026-08-26T20:10:02.069079-06:00: 1097 reg, 142 cutoff headcount, 175 attendees including late arrivals, 48 route deals (46 Master Class sold + 2 futures).'
  },
  {
    market: 'Portland',
    team: 'Team Vogel · Speaker Tony / #teamvogel',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 738,
    attendedCutoff: 70,
    sales: 24,
    routeDeals: 24,
    previewShowRate: 70 / 738,
    salesRate: 24 / 70,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-22',
    latestSessionDate: '2026-08-25',
    sourcePostedAt: '2026-08-25T21:33:23.468589-06:00',
    sourceNote: 'Final route report from #teamvogel, labeled Team Vogel, at 2026-08-25T21:33:23.468589-06:00: 738 reg, 70 cutoff headcount, 74 attendees including late arrivals, 24 route deals (24 Master Class sold + 0 futures).'
  },
  {
    market: 'Charlotte',
    team: 'Team Millar · Speaker Jay / #teammillar',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 991,
    attendedCutoff: 159,
    sales: 40,
    routeDeals: 47,
    previewShowRate: 159 / 991,
    salesRate: 47 / 159,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-22',
    latestSessionDate: '2026-08-25',
    sourcePostedAt: '2026-08-25T18:48:45.599939-06:00',
    sourceNote: 'Final route report from #teammillar, labeled Team Millar, at 2026-08-25T18:48:45.599939-06:00: 991 reg, 159 cutoff headcount, 172 attendees including late arrivals, 47 route deals (40 Master Class sold + 7 futures).'
  },
  {
    market: 'San Francisco, California',
    team: 'Team Vogel · Speaker Tony / #teamvogel',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 1106,
    attendedCutoff: 124,
    sales: 58,
    routeDeals: 59,
    previewShowRate: 124 / 1106,
    salesRate: 59 / 124,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-15',
    latestSessionDate: '2026-08-19',
    sourcePostedAt: '2026-08-19T21:56:44.512629-06:00',
    sourceNote: 'Final route report from #teamvogel, labeled Team Vogel, at 2026-08-19T21:56:44.512629-06:00: 1106 reg, 124 cutoff headcount, 165 attendees including late arrivals, 59 route deals (58 Master Class sold + 1 futures).'
  },
  {
    market: 'Little Rock',
    team: 'Team Gray · Speaker Nick / #teamwayne',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 1047,
    attendedCutoff: 146,
    sales: 40,
    routeDeals: 43,
    previewShowRate: 146 / 1047,
    salesRate: 43 / 146,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-15',
    latestSessionDate: '2026-08-18',
    sourcePostedAt: '2026-08-18T19:44:44.962649-06:00',
    sourceNote: 'Final route report from #teamwayne, labeled Team Gray, at 2026-08-18T19:44:44.962649-06:00: 1047 reg, 146 cutoff headcount, 148 attendees including late arrivals, 43 route deals (40 Master Class sold + 3 futures).'
  },
  {
    market: 'Greenville',
    team: 'Team Dent · Speaker Jay / #teamdent',
    sessionsCompleted: null,
    totalSessions: null,
    registered: 885,
    attendedCutoff: 157,
    sales: 27,
    routeDeals: 28,
    previewShowRate: 157 / 885,
    salesRate: 28 / 157,
    status: 'yellow',
    sourceState: 'final_route_totals',
    startDate: '2026-08-15',
    latestSessionDate: '2026-08-18',
    sourcePostedAt: '2026-08-18T18:46:47.777929-06:00',
    sourceNote: 'Final route report from #teamdent, labeled Team Dent, at 2026-08-18T18:46:47.777929-06:00: 885 reg, 157 cutoff headcount, 170 attendees including late arrivals, 28 route deals (27 Master Class sold + 1 futures).'
  }
];

export const activeMarketingMarkets: ActiveMarketingMarket[] = [
  {
    market: 'Charlotte',
    startDate: '2026-08-22',
    starts: 'Saturday August 22nd',
    channels: [
      { channel: 'Facebook', regs: 741, spend: 35491, cpr: 48 },
      { channel: 'YouTube', regs: 155, spend: 8963, cpr: 58 },
      { channel: 'Google Search', regs: 15, spend: 809, cpr: 54 },
      { channel: 'Total', regs: 911, spend: 45264, cpr: 50 }
    ]
  },
  {
    market: 'Portland',
    startDate: '2026-08-22',
    starts: 'Saturday August 22nd',
    channels: [
      { channel: 'Facebook', regs: 517, spend: 31338, cpr: 61 },
      { channel: 'YouTube', regs: 149, spend: 9295, cpr: 62 },
      { channel: 'Google Search', regs: 14, spend: 464, cpr: 33 },
      { channel: 'Total', regs: 680, spend: 41097, cpr: 60 }
    ]
  },
  {
    market: 'St. Louis',
    startDate: '2026-08-22',
    starts: 'Saturday August 22nd',
    channels: [
      { channel: 'Facebook', regs: 820, spend: 34848, cpr: 42 },
      { channel: 'YouTube', regs: 168, spend: 9286, cpr: 55 },
      { channel: 'Google Search', regs: 10, spend: 1077, cpr: 108 },
      { channel: 'Total', regs: 998, spend: 45211, cpr: 45 }
    ]
  },
  {
    market: 'Atlanta',
    startDate: '2026-08-29',
    starts: 'Saturday August 29th',
    channels: [
      { channel: 'Facebook', regs: 888, spend: 26931, cpr: 30 },
      { channel: 'YouTube', regs: 362, spend: 11616, cpr: 32 },
      { channel: 'Google Search', regs: 28, spend: 1685, cpr: 60 },
      { channel: 'Total', regs: 1347, spend: 43167, cpr: 32 }
    ]
  },
  {
    market: 'White Plains',
    startDate: '2026-08-29',
    starts: 'Saturday August 29th',
    channels: [
      { channel: 'Facebook', regs: 754, spend: 26919, cpr: 36 },
      { channel: 'YouTube', regs: 259, spend: 11702, cpr: 45 },
      { channel: 'Google Search', regs: 12, spend: 1089, cpr: 91 },
      { channel: 'Total', regs: 1070, spend: 42362, cpr: 40 }
    ]
  },
  {
    market: 'Baltimore',
    startDate: '2026-09-09',
    starts: 'Wednesday September 9th',
    channels: [
      { channel: 'Facebook', regs: 551, spend: 14264, cpr: 26 },
      { channel: 'YouTube', regs: 108, spend: 4129, cpr: 38 },
      { channel: 'Google Search', regs: 13, spend: 711, cpr: 55 },
      { channel: 'Total', regs: 706, spend: 20354, cpr: 29 }
    ]
  },
  {
    market: 'Newark',
    startDate: '2026-09-09',
    starts: 'Wednesday September 9th',
    channels: [
      { channel: 'Facebook', regs: 524, spend: 13441, cpr: 26 },
      { channel: 'YouTube', regs: 97, spend: 4000, cpr: 41 },
      { channel: 'Google Search', regs: 6, spend: 1199, cpr: 200 },
      { channel: 'Total', regs: 659, spend: 19880, cpr: 30 }
    ]
  },
  {
    market: 'Richmond',
    startDate: '2026-09-09',
    starts: 'Wednesday September 9th',
    channels: [
      { channel: 'Facebook', regs: 360, spend: 14852, cpr: 41 },
      { channel: 'YouTube', regs: 82, spend: 4449, cpr: 54 },
      { channel: 'Google Search', regs: 3, spend: 132, cpr: 44 },
      { channel: 'Total', regs: 463, spend: 20834, cpr: 45 }
    ]
  },
  {
    market: 'Norfolk',
    startDate: '2026-09-13',
    starts: 'Sunday September 13th',
    channels: [
      { channel: 'Facebook', regs: 250, spend: 7786, cpr: 31 },
      { channel: 'YouTube', regs: 52, spend: 2353, cpr: 45 },
      { channel: 'Google Search', regs: 1, spend: 185, cpr: 185 },
      { channel: 'Total', regs: 326, spend: 11135, cpr: 34 }
    ]
  },
  {
    market: 'Philadelphia',
    startDate: '2026-09-13',
    starts: 'Sunday September 13th',
    channels: [
      { channel: 'Facebook', regs: 312, spend: 6998, cpr: 22 },
      { channel: 'YouTube', regs: 83, spend: 2075, cpr: 25 },
      { channel: 'Google Search', regs: 4, spend: 260, cpr: 65 },
      { channel: 'Total', regs: 429, spend: 10020, cpr: 23 }
    ]
  },
  {
    market: 'Washington DC',
    startDate: '2026-09-13',
    starts: 'Sunday September 13th',
    channels: [
      { channel: 'Facebook', regs: 184, spend: 7899, cpr: 43 },
      { channel: 'YouTube', regs: 63, spend: 2327, cpr: 37 },
      { channel: 'Google Search', regs: 5, spend: 226, cpr: 45 },
      { channel: 'Total', regs: 275, spend: 11160, cpr: 41 }
    ]
  }
];

export const middleEndSummary: MiddleEndSummary[] = [
  { label: 'Final ME', period: 'Last week', market: 'Boise, ID', team: 'Team Nick · Speaker Nick', sold: 31, attended: 30, showRate: 30 / 31, startDate: '2026-08-23', workshopSales: 11, sourceNote: 'Live preview-sold source from #teamnick at 2026-08-20T09:34:16.889919-06:00: 31 buyers sold. Final workshop post from #teamnick shows 30 BU attended and 11 ME sales.' },
  { label: 'Final ME', period: 'Last week', market: 'Grand Rapids, MI', team: 'Team Tony · Speaker Tony', sold: 39, attended: 33, showRate: 33 / 39, startDate: '2026-08-23', workshopSales: 17, sourceNote: 'Live preview-sold source from #teamtony at 2026-08-20T09:27:08.589939-06:00: 39 buyers sold. Final workshop post from #teamtony shows 33 BU attended and 17 ME sales.' },
  { label: 'Final ME', period: 'Last week', market: 'Chicago, IL', team: 'Team Tony · Speaker Tony', sold: 56, attended: 51, showRate: 51 / 56, startDate: '2026-08-16', workshopSales: 22, sourceNote: 'Live preview-sold source from #teamtony at 2026-08-12T12:00:43.748369-06:00: 56 buyers sold. Final workshop post from #teamtony shows 51 BU attended and 22 ME sales.' },
  { label: 'Final ME', period: 'Last week', market: 'Denver, CO', team: 'Team Drecksel · Speaker Drecksel', sold: 31, attended: 26, showRate: 26 / 31, startDate: '2026-08-16', workshopSales: 11, sourceNote: 'Live preview-sold source from #teamdrecksel at 2026-08-13T13:28:28.982459-06:00: 31 buyers sold. Final workshop post from #teamdrecksel shows 26 BU attended and 11 ME sales.' },
  { label: 'Final ME', period: 'Last week', market: 'Indianapolis, IN', team: 'Team Shaw · Speaker Shaw', sold: 45, attended: 43, showRate: 43 / 45, startDate: '2026-08-16', workshopSales: 18, sourceNote: 'Live preview-sold source from #teamshaw at 2026-08-12T12:12:39.002889-06:00: 45 buyers sold. Final workshop post from #teamshaw shows 43 BU attended and 18 ME sales.' },
  { label: 'Final ME', period: 'Last week', market: 'Hartford, CT', team: 'Team Tony · Speaker Tony', sold: 56, attended: 52, showRate: 52 / 56, startDate: '2026-08-02', workshopSales: 23, sourceNote: 'Live preview-sold source from #teamtony at 2026-07-30T12:19:38.076189-06:00: 56 buyers sold. Final workshop post from #teamtony shows 52 BU attended and 23 ME sales.' }
];

export const upcomingMePipeline: UpcomingMePipelineMarket[] = [
  {
    market: 'Ann Arbor, MI',
    previewTeam: 'Team Vogel / #teamvogel',
    middleEndTeam: 'Team Tony',
    startDate: '2026-08-28',
    endDate: '2026-08-30',
    previewSold: 50,
    projectedBuyingUnits: 51,
    middleEndSold: null,
    source: 'Workshop Team Scheduling plus #teamtony current floor count at 2026-08-28T08:30:29.317829-06:00: 50 preview sold; 51 BU on site and 19 guests. ME sold remains pending until the final Event Stats post lands.',
    sourcePostedAt: '2026-08-28T08:30:29.317829-06:00'
  },
  {
    market: 'Raleigh, NC',
    previewTeam: 'Team Wayne / #teamwayne',
    middleEndTeam: 'Team Shaw',
    startDate: '2026-08-28',
    endDate: '2026-08-30',
    previewSold: 35,
    projectedBuyingUnits: 35,
    middleEndSold: null,
    source: 'Workshop Team Scheduling plus #teamshaw current floor count at 2026-08-28T08:38:56.181799-06:00: 35 preview sold; 35 BU on site. ME sold remains pending until the final Event Stats post lands.',
    sourcePostedAt: '2026-08-28T08:38:56.181799-06:00'
  },
  {
    market: 'Sacramento',
    previewTeam: 'Team Vogel / #teamvogel',
    middleEndTeam: 'Team Drexel',
    startDate: '2026-08-28',
    endDate: '2026-08-30',
    previewSold: 34,
    projectedBuyingUnits: 27,
    middleEndSold: null,
    source: 'Workshop Team Scheduling plus #teamdrecksel current floor count at 2026-08-28T11:30:09.241479-06:00: 34 preview sold; 27 BU on site and 10 guests. ME sold remains pending until the final Event Stats post lands.',
    sourcePostedAt: '2026-08-28T11:30:09.241479-06:00'
  },
  {
    market: 'Fremont, CA',
    previewTeam: 'Pending preview source',
    middleEndTeam: 'Team Tony',
    startDate: '2026-09-03',
    endDate: '2026-09-05',
    previewSold: null,
    projectedBuyingUnits: null,
    middleEndSold: null,
    source: 'Workshop Team Scheduling defines this upcoming route. Preview sold and confirmed BU are pending until a matching team update or preview final is available; ME sold remains pending until the final Event Stats post.',
    sourcePostedAt: '2026-08-29T08:07:21-06:00'
  },
  {
    market: 'Greenville, SC',
    previewTeam: 'Team Dent / #teamdent',
    middleEndTeam: 'Team Drexel',
    startDate: '2026-09-03',
    endDate: '2026-09-05',
    previewSold: 28,
    projectedBuyingUnits: null,
    middleEndSold: null,
    source: 'Workshop Team Scheduling plus #teamdent preview final: 28 buyers sold. Confirmed BU are pending until the matching ME team update; ME sold remains pending until the final Event Stats post.',
    sourcePostedAt: '2026-08-29T08:07:21-06:00'
  },
  {
    market: 'Little Rock, AR',
    previewTeam: 'Team Wayne / #teamwayne',
    middleEndTeam: 'Team Nick',
    startDate: '2026-09-03',
    endDate: '2026-09-05',
    previewSold: 43,
    projectedBuyingUnits: null,
    middleEndSold: null,
    source: 'Workshop Team Scheduling plus #teamwayne preview final: 43 buyers sold. Confirmed BU are pending until the matching ME team update; ME sold remains pending until the final Event Stats post.',
    sourcePostedAt: '2026-08-29T08:07:21-06:00'
  }
];
