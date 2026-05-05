export type MarketingHistoryRun = {
  market: string;
  eventDate: string;
  registrations: number | null;
  spend: number | null;
  cpr: number | null;
  notes?: string;
};

export type PreviewSessionRow = {
  market: 'Atlanta' | 'Norfolk';
  team: string;
  session: string;
  reg: number;
  attendance: number;
  sales: number;
};

export type TeamPreviewHistoryRow = {
  team: 'Team Dent' | 'Team Vogel' | 'Team Wayne' | 'Team Wyman';
  market: string;
  date: string;
  reg: number;
  attended: number;
  showRate: number;
  salesRate: number;
  buyingUnits: number | null;
  sold: number;
  workshopAttendance: number | null;
};

export type MiddleEndCurrentWorkshop = {
  market: string;
  team: string;
  eventDate: string;
  buyingUnits: number;
  soldClosed: number | null;
  showed: number;
  totalWritten: number | null;
  totalCollected: number | null;
  abcBreakdown: string | null;
  notes?: string;
};

export type MiddleEndHistoricalRow = {
  team: 'Team Tony' | 'Team Drexel' | 'Team Shaw' | 'Team Nick';
  market: string;
  date: string;
  buyingUnits: number;
  soldClosed: number | null;
  totalWritten: number | null;
  totalCollected: number | null;
  abcBreakdown: string | null;
  otherStats?: string;
};

export type InsideSalesRepRow = {
  rep: string;
  leads: number | null;
  revenue: number | null;
  dpl: number | null;
  collected: number | null;
  collectedDpl: number | null;
  source: string;
};

export type InsideSalesSourceRow = {
  source: string;
  leads: number | null;
  revenue: number | null;
  pendingCollections: number | null;
  ytdCollections: number | null;
  sixWeekYtd: number | null;
  tenWeekYtd: number | null;
};

export type SpeakerCollectionRow = {
  speaker: string;
  amountIntoCollections: number | null;
  collectionsOut: number | null;
  pendingOutstanding: number | null;
  dplOrCollectionMetric: string | null;
};

export const marketingHistory: Record<string, MarketingHistoryRun[]> = {
  Raleigh: [
    { market: 'Raleigh', eventDate: '2026-01-10–13', registrations: 3979, spend: null, cpr: null, notes: 'Numbers Per Session rollup; spend/CPR source pending.' },
    { market: 'Raleigh', eventDate: '2025-08-02–06', registrations: null, spend: null, cpr: null, notes: 'Historical run located in session source; marketing spend source pending.' },
    { market: 'Raleigh', eventDate: '2023-04-15', registrations: null, spend: null, cpr: null, notes: 'Older run located in session source; marketing spend source pending.' },
  ],
  Tampa: [
    { market: 'Tampa', eventDate: '2025-12-07–11', registrations: 12022, spend: null, cpr: null, notes: 'Numbers Per Session rollup; spend/CPR source pending.' },
    { market: 'Tampa', eventDate: '2025-07-13–17', registrations: null, spend: null, cpr: null, notes: 'Historical run located in session source; marketing spend source pending.' },
    { market: 'Tampa', eventDate: 'source pending', registrations: null, spend: null, cpr: null, notes: 'Need prior tracker/export for third comparable run.' },
  ],
  'West Palm Beach': [
    { market: 'West Palm Beach', eventDate: 'source pending', registrations: null, spend: null, cpr: null, notes: 'Need prior tracker/export for a completed comparable run; current May run is active, not history.' },
    { market: 'West Palm Beach', eventDate: '2025-11-08–12', registrations: null, spend: null, cpr: null, notes: 'Historical run located in session source; marketing spend source pending.' },
    { market: 'West Palm Beach', eventDate: 'source pending', registrations: null, spend: null, cpr: null, notes: 'Need prior tracker/export for third comparable run.' },
  ],
};

export const previewSessions: PreviewSessionRow[] = [
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 1', reg: 148, attendance: 18, sales: 7 },
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 2', reg: 310, attendance: 52, sales: 18 },
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 3', reg: 227, attendance: 20, sales: 6 },
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 4', reg: 477, attendance: 35, sales: 8 },
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 5', reg: 121, attendance: 19, sales: 5 },
  { market: 'Atlanta', team: 'Team Vogel', session: 'Session 6', reg: 128, attendance: 18, sales: 2 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 1', reg: 126, attendance: 21, sales: 7 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 2', reg: 246, attendance: 25, sales: 7 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 3', reg: 157, attendance: 19, sales: 9 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 4', reg: 281, attendance: 43, sales: 14 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 5', reg: 74, attendance: 8, sales: 2 },
  { market: 'Norfolk', team: 'Team Dent', session: 'Session 6', reg: 152, attendance: 16, sales: 1 },
];

export const teamPreviewHistory: TeamPreviewHistoryRow[] = [
  { team: 'Team Dent', market: 'Richmond', date: '2026-04-28', reg: 1532, attended: 173, showRate: 0.1129, salesRate: 0.289, buyingUnits: null, sold: 50, workshopAttendance: 49 },
  { team: 'Team Dent', market: 'Denver', date: '2026-04-01', reg: 733, attended: 77, showRate: 0.105, salesRate: 0.312, buyingUnits: null, sold: 24, workshopAttendance: 21 },
  { team: 'Team Dent', market: 'Orange County', date: '2026-02-24', reg: 1132, attended: 166, showRate: 0.1466, salesRate: 0.283, buyingUnits: null, sold: 47, workshopAttendance: null },
  { team: 'Team Dent', market: 'Atlanta', date: '2026-01-21', reg: 1677, attended: 236, showRate: 0.1407, salesRate: 0.258, buyingUnits: null, sold: 61, workshopAttendance: null },
  { team: 'Team Dent', market: 'Charleston', date: '2026-01-13', reg: 1397, attended: 203, showRate: 0.1453, salesRate: 0.296, buyingUnits: null, sold: 60, workshopAttendance: null },
  { team: 'Team Dent', market: 'Phoenix', date: '2025-11-05', reg: 1232, attended: 176, showRate: 0.1356, salesRate: 0.275, buyingUnits: null, sold: 46, workshopAttendance: null },

  { team: 'Team Vogel', market: 'Los Angeles', date: '2026-04-22', reg: 1624, attended: 171, showRate: 0.1053, salesRate: 0.409, buyingUnits: null, sold: 70, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Phoenix', date: '2026-04-15', reg: 968, attended: 82, showRate: 0.0847, salesRate: 0.378, buyingUnits: null, sold: 31, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Tucson', date: '2026-04-11', reg: 620, attended: 85, showRate: 0.1371, salesRate: 0.341, buyingUnits: null, sold: 29, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Indianapolis', date: '2026-04-01', reg: 1029, attended: 112, showRate: 0.1088, salesRate: 0.446, buyingUnits: null, sold: 50, workshopAttendance: null },
  { team: 'Team Vogel', market: 'DC', date: '2026-03-11', reg: 1142, attended: 107, showRate: 0.0937, salesRate: 0.533, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Hartford', date: '2026-03-04', reg: 1363, attended: 201, showRate: 0.1475, salesRate: 0.393, buyingUnits: null, sold: 79, workshopAttendance: 76 },

  { team: 'Team Wayne', market: 'Chicago', date: '2026-04-29', reg: 1583, attended: 216, showRate: 0.1364, salesRate: 0.315, buyingUnits: null, sold: 67, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Long Island', date: '2026-04-22', reg: 1832, attended: 204, showRate: 0.1114, salesRate: 0.387, buyingUnits: null, sold: 79, workshopAttendance: 76 },
  { team: 'Team Wayne', market: 'Los Angeles', date: '2026-04-15', reg: 1922, attended: 233, showRate: 0.1212, salesRate: 0.395, buyingUnits: null, sold: 92, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Philadelphia', date: '2026-04-01', reg: 1549, attended: 156, showRate: 0.1007, salesRate: 0.423, buyingUnits: null, sold: 64, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Boston', date: '2026-03-25', reg: 947, attended: 113, showRate: 0.1193, salesRate: 0.496, buyingUnits: null, sold: 56, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Dallas', date: '2026-03-11', reg: 1177, attended: 162, showRate: 0.1376, salesRate: 0.34, buyingUnits: null, sold: 55, workshopAttendance: null },

  { team: 'Team Wyman', market: 'Orlando', date: '2026-03-24', reg: 1081, attended: 141, showRate: 0.1304, salesRate: 0.404, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Memphis', date: '2026-03-10', reg: 1661, attended: 297, showRate: 0.1788, salesRate: 0.226, buyingUnits: null, sold: 67, workshopAttendance: 67 },
  { team: 'Team Wyman', market: 'Jacksonville', date: '2026-03-03', reg: 940, attended: 132, showRate: 0.1404, salesRate: 0.265, buyingUnits: null, sold: 33, workshopAttendance: null },
  { team: 'Team Wyman', market: 'San Diego', date: '2026-02-17', reg: 874, attended: 111, showRate: 0.127, salesRate: 0.306, buyingUnits: null, sold: 32, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Las Vegas', date: '2026-02-11', reg: 1397, attended: 206, showRate: 0.1475, salesRate: 0.301, buyingUnits: null, sold: 62, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Greenville', date: '2026-01-28', reg: 405, attended: 60, showRate: 0.1481, salesRate: 0.333, buyingUnits: null, sold: 20, workshopAttendance: 17 },
];

export const currentMiddleEndWorkshops: MiddleEndCurrentWorkshop[] = [
  { market: 'LA2', team: 'Team Tony', eventDate: '2026-05-01', buyingUnits: 38, soldClosed: null, showed: 30, totalWritten: null, totalCollected: null, abcBreakdown: null, notes: 'Show-up verified from Slack check-in; final written/collected/ABC workshop report source pending.' },
  { market: 'Phoenix', team: 'Team Shaw', eventDate: '2026-05-01', buyingUnits: 29, soldClosed: null, showed: 23, totalWritten: null, totalCollected: null, abcBreakdown: null, notes: 'Show-up verified from Slack check-in; final written/collected/ABC workshop report source pending.' },
];

export const middleEndHistory: MiddleEndHistoricalRow[] = [
  { team: 'Team Tony', market: 'LA2', date: '2026-05-01', buyingUnits: 38, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: '30 showed buying units; final workshop report pending.' },
  { team: 'Team Tony', market: 'Tucson', date: '2026-04-24', buyingUnits: 29, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Schedule/source row available; final ME report pending.' },
  { team: 'Team Tony', market: 'Long Island', date: '2026-04-24', buyingUnits: 79, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Preview buyers source available; ME close report pending.' },

  { team: 'Team Drexel', market: 'LA1', date: '2026-04-24', buyingUnits: 50, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: '41 showed buying units confirmed final; no ABC/collections source in current model.' },
  { team: 'Team Drexel', market: 'Source pending', date: 'source pending', buyingUnits: 0, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Need final workshop/ME reports for additional last-6 rows.' },

  { team: 'Team Shaw', market: 'Phoenix', date: '2026-05-01', buyingUnits: 29, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: '23 showed buying units; final workshop report pending.' },
  { team: 'Team Shaw', market: 'Source pending', date: 'source pending', buyingUnits: 0, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Need final workshop/ME reports for additional last-6 rows.' },

  { team: 'Team Nick', market: 'Nashville', date: '2026-01-23', buyingUnits: 52, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Workshop attendance noted in preview final; final ME report pending.' },
  { team: 'Team Nick', market: 'Charlotte', date: '2026-01-09', buyingUnits: 65, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Workshop attendance noted in preview final; final ME report pending.' },
  { team: 'Team Nick', market: 'Greenville', date: '2026-01-30', buyingUnits: 20, soldClosed: null, totalWritten: null, totalCollected: null, abcBreakdown: null, otherStats: 'Workshop attendance noted in preview final; final ME report pending.' },
];

export const insideSalesSourceCategories: InsideSalesSourceRow[] = [
  'BB Cancelled', 'RNA', 'BB / Buyer', 'Buyer paid-in-full collections', 'BB PIF', 'Event', 'Expo collections', 'Buyer', 'Buyer collections', 'Jumpstart pending'
].map((source) => ({ source, leads: null, revenue: null, pendingCollections: null, ytdCollections: null, sixWeekYtd: null, tenWeekYtd: null }));

export const insideSalesRepRows: InsideSalesRepRow[] = [
  { rep: 'Team Travis reps', leads: null, revenue: null, dpl: null, collected: null, collectedDpl: null, source: 'UTL app/performance dashboard source pending' },
  { rep: 'Team Curt reps', leads: null, revenue: null, dpl: null, collected: null, collectedDpl: null, source: 'UTL app/performance dashboard source pending' },
];

export const speakerCollectionRows: SpeakerCollectionRow[] = ['Tony', 'Drexel', 'Shaw', 'Nick', 'Megan', 'Jazey'].map((speaker) => ({ speaker, amountIntoCollections: null, collectionsOut: null, pendingOutstanding: null, dplOrCollectionMetric: null }));
