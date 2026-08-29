export const insideSalesSourceUpdatedAt = '2026-08-29T14:06:39.701Z';
export const collectionsSourceFetchedAt = '2026-08-29T06:04:55.955799-06:00';

export type MarketingHistoryChannel = {
  channel: string;
  registrations: number;
  attended?: number;
  buyers?: number;
  spend: number;
  cpr: number | null;
};

export type MarketingHistoryRun = {
  market: string;
  eventDate: string;
  registrations: number | null;
  attended?: number | null;
  sold?: number | null;
  spend: number | null;
  cpr: number | null;
  channels: MarketingHistoryChannel[];
  notes?: string;
};

export type PreviewSessionRow = {
  market: string;
  team: string;
  session: string;
  speaker: string;
  reg: number;
  attendance: number;
  sales: number;
};

export type TeamPreviewHistoryRow = {
  team: 'Team Dent' | 'Team Millar' | 'Team Vogel' | 'Team Wayne' | 'Team Wyman';
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
  dpl: number | null;
  revenueShare: number | null;
};

export type SpeakerCollectionRow = {
  speaker: string;
  amountIntoCollections: number | null;
  collectionsOut: number | null;
  pendingOutstanding: number | null;
  sixWeekCollected: number | null;
  tenWeekCollected: number | null;
  dplOrCollectionMetric: string | null;
};

export const marketingHistory: Record<string, MarketingHistoryRun[]> = {
  Raleigh: [
    { market: 'Raleigh', eventDate: 'Jan 10, 2026', registrations: 1329, spend: 44827, cpr: 33.73, channels: [
      { channel: 'Facebook', registrations: 892, spend: 25000, cpr: 28.03 },
      { channel: 'YouTube', registrations: 421, spend: 19827, cpr: 47.10 },
      { channel: 'Total', registrations: 1329, spend: 44827, cpr: 33.73 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Raleigh', eventDate: 'Aug 2, 2025', registrations: 1189, spend: 42460.16, cpr: 35.71, channels: [
      { channel: 'Facebook', registrations: 749, spend: 25612.02, cpr: 34.19 },
      { channel: 'YouTube', registrations: 411, spend: 15615.52, cpr: 37.99 },
      { channel: 'TikTok', registrations: 20, spend: 1232.62, cpr: 61.63 },
      { channel: 'Total', registrations: 1189, spend: 42460.16, cpr: 35.71 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Raleigh-Durham', eventDate: 'Jan 26, 2025', registrations: 1323, spend: 43805.58, cpr: 33.11, channels: [
      { channel: 'Facebook', registrations: 840, spend: 25856.65, cpr: 30.78 },
      { channel: 'YouTube', registrations: 483, spend: 17948.93, cpr: 37.16 },
      { channel: 'Total', registrations: 1323, spend: 43805.58, cpr: 33.11 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed comparable run.' },
  ],
  Tampa: [
    { market: 'Tampa', eventDate: 'Dec 7, 2025', registrations: 1246, spend: 40409.7, cpr: 32.43, channels: [
      { channel: 'Facebook', registrations: 830, spend: 24999.57, cpr: 30.12 },
      { channel: 'YouTube', registrations: 406, spend: 15410.13, cpr: 37.96 },
      { channel: 'Total', registrations: 1246, spend: 40409.7, cpr: 32.43 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Tampa', eventDate: 'Jul 12, 2025', registrations: 1212, spend: 43192.68, cpr: 35.64, channels: [
      { channel: 'Facebook', registrations: 729, spend: 20000, cpr: 27.43 },
      { channel: 'YouTube', registrations: 435, spend: 21087.66, cpr: 48.48 },
      { channel: 'TikTok', registrations: 41, spend: 2105.02, cpr: 51.34 },
      { channel: 'Total', registrations: 1212, spend: 43192.68, cpr: 35.64 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Tampa', eventDate: 'Feb 23, 2025', registrations: 1327, spend: 38306.99, cpr: 28.87, channels: [
      { channel: 'Facebook', registrations: 798, spend: 18416.29, cpr: 23.08 },
      { channel: 'YouTube', registrations: 529, spend: 19890.7, cpr: 37.60 },
      { channel: 'Total', registrations: 1327, spend: 38306.99, cpr: 28.87 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
  ],
  'West Palm Beach': [
    { market: 'West Palm Beach (TDAI)', eventDate: 'Jan 24, 2026', registrations: 1001, spend: 38375.31, cpr: 38.34, channels: [
      { channel: 'Facebook', registrations: 761, spend: 24975.31, cpr: 32.82 },
      { channel: 'YouTube', registrations: 236, spend: 13400, cpr: 56.78 },
      { channel: 'Total', registrations: 1001, spend: 38375.31, cpr: 38.34 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed comparable run.' },
    { market: 'West Palm Beach', eventDate: 'Nov 8, 2025', registrations: 1252, spend: 45152.96, cpr: 36.06, channels: [
      { channel: 'Facebook', registrations: 815, spend: 31851.05, cpr: 39.08 },
      { channel: 'YouTube', registrations: 426, spend: 13301.91, cpr: 31.23 },
      { channel: 'Total', registrations: 1252, spend: 45152.96, cpr: 36.06 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'West Palm Beach', eventDate: 'Apr 5, 2025', registrations: 1379, spend: 39609.26, cpr: 28.72, channels: [
      { channel: 'Facebook', registrations: 829, spend: 20000, cpr: 24.13 },
      { channel: 'YouTube', registrations: 550, spend: 19609.26, cpr: 35.65 },
      { channel: 'Total', registrations: 1379, spend: 39609.26, cpr: 28.72 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
  ],
  Minneapolis: [
    { market: 'Minneapolis', eventDate: 'Oct 11, 2025', registrations: 1120, spend: 47255.99, cpr: 42.19, channels: [
      { channel: 'Facebook', registrations: 686, spend: 26272.16, cpr: 38.30 },
      { channel: 'YouTube', registrations: 387, spend: 18153.98, cpr: 46.91 },
      { channel: 'Total', registrations: 1120, spend: 47255.99, cpr: 42.19 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Minneapolis', eventDate: 'May 3, 2025', registrations: 1103, spend: 40780.39, cpr: 36.97, channels: [
      { channel: 'Facebook', registrations: 737, spend: 25000, cpr: 33.92 },
      { channel: 'YouTube', registrations: 366, spend: 15780.39, cpr: 43.12 },
      { channel: 'Total', registrations: 1103, spend: 40780.39, cpr: 36.97 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
    { market: 'Minneapolis', eventDate: 'Jul 21, 2024', registrations: 1012, spend: 35317.55, cpr: 34.90, channels: [
      { channel: 'Facebook', registrations: 982, spend: 35163.90, cpr: 35.81 },
      { channel: 'YouTube', registrations: 9, spend: 153.65, cpr: 17.07 },
      { channel: 'Total', registrations: 1012, spend: 35317.55, cpr: 34.90 },
    ], notes: 'TLWB Live Event Numbers master tracker — completed same-city run.' },
  ],
};

export const previewSessions: PreviewSessionRow[] = [
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 2 Session 1', speaker: 'Jay', reg: 121, attendance: 20, sales: 1 },
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 2 Session 2', speaker: 'Jay', reg: 179, attendance: 30, sales: 9 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 2 Session 1', speaker: 'Tony', reg: 58, attendance: 5, sales: 3 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 2 Session 2', speaker: 'Tony', reg: 71, attendance: 7, sales: 2 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 2 Session 1', speaker: 'Nick', reg: 94, attendance: 20, sales: 5 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 2 Session 2', speaker: 'Nick', reg: 110, attendance: 16, sales: 7 },
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 3 Session 1', speaker: 'Jay', reg: 110, attendance: 12, sales: 2 },
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 3 Session 2', speaker: 'Jay', reg: 110, attendance: 14, sales: 6 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 3 Session 1', speaker: 'Tony', reg: 106, attendance: 10, sales: 4 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 3 Session 2', speaker: 'Tony', reg: 58, attendance: 5, sales: 2 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 3 Session 1', speaker: 'Nick', reg: 156, attendance: 23, sales: 9 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 3 Session 2', speaker: 'Nick', reg: 139, attendance: 22, sales: 5 },
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 4 Session 1', speaker: 'Jay', reg: 53, attendance: 5, sales: 2 },
  { market: 'Charlotte', team: 'Team Millar', session: 'Day 4 Session 2', speaker: 'Jay', reg: 53, attendance: 20, sales: 8 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 4 Session 1', speaker: 'Tony', reg: 119, attendance: 15, sales: 4 },
  { market: 'Portland', team: 'Team Vogel', session: 'Day 4 Session 2', speaker: 'Tony', reg: 164, attendance: 15, sales: 6 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 4 Session 1', speaker: 'Nick', reg: 125, attendance: 11, sales: 1 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 4 Session 2', speaker: 'Nick', reg: 72, attendance: 7, sales: 3 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 5 Session 1', speaker: 'Nick', reg: 104, attendance: 5, sales: 4 },
  { market: 'St. Louis, MO', team: 'Team Wayne', session: 'Day 5 Session 2', speaker: 'Wayne', reg: 102, attendance: 13, sales: 0 }
];

export const teamPreviewHistory: TeamPreviewHistoryRow[] = [
  { team: 'Team Wayne', market: 'St. Louis, MO', date: '2026-08-26', reg: 1097, attended: 142, showRate: 142 / 1097, salesRate: 48 / 142, buyingUnits: 45, sold: 48, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Portland', date: '2026-08-25', reg: 738, attended: 70, showRate: 70 / 738, salesRate: 24 / 70, buyingUnits: null, sold: 24, workshopAttendance: null },
  { team: 'Team Millar', market: 'Charlotte', date: '2026-08-25', reg: 991, attended: 159, showRate: 159 / 991, salesRate: 47 / 159, buyingUnits: null, sold: 47, workshopAttendance: null },
  { team: 'Team Vogel', market: 'San Francisco, CA', date: '2026-08-19', reg: 1106, attended: 124, showRate: 124 / 1106, salesRate: 59 / 124, buyingUnits: 59, sold: 59, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Little Rock', date: '2026-08-18', reg: 1047, attended: 146, showRate: 146 / 1047, salesRate: 43 / 146, buyingUnits: null, sold: 43, workshopAttendance: null },
  { team: 'Team Dent', market: 'Greenville', date: '2026-08-18', reg: 885, attended: 157, showRate: 157 / 885, salesRate: 28 / 157, buyingUnits: null, sold: 28, workshopAttendance: null },
  { team: 'Team Millar', market: 'Boise, Idaho', date: '2026-08-12', reg: 460, attended: 106, showRate: 106 / 460, salesRate: 37 / 106, buyingUnits: 31, sold: 37, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Raleigh', date: '2026-08-12', reg: 888, attended: 93, showRate: 93 / 888, salesRate: 35 / 93, buyingUnits: null, sold: 35, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Ann Arbor', date: '2026-08-12', reg: 1421, attended: 131, showRate: 131 / 1421, salesRate: 53 / 131, buyingUnits: null, sold: 53, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Sacramento', date: '2026-08-04', reg: 1105, attended: 76, showRate: 76 / 1105, salesRate: 30 / 76, buyingUnits: null, sold: 30, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Grand Rapids', date: '2026-08-04', reg: 1149, attended: 143, showRate: 143 / 1149, salesRate: 39 / 143, buyingUnits: null, sold: 39, workshopAttendance: null },
  { team: 'Team Millar', market: 'Chicago', date: '2026-07-29', reg: 1535, attended: 236, showRate: 236 / 1535, salesRate: 57 / 236, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Indianapolis IN', date: '2026-07-29', reg: 1037, attended: 108, showRate: 108 / 1037, salesRate: 47 / 108, buyingUnits: 45, sold: 47, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Denver', date: '2026-07-28', reg: 895, attended: 79, showRate: 79 / 895, salesRate: 31 / 79, buyingUnits: null, sold: 31, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Hartford', date: '2026-07-15', reg: 1233, attended: 137, showRate: 137 / 1233, salesRate: 58 / 137, buyingUnits: null, sold: 58, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Memphis', date: '2026-07-15', reg: 1745, attended: 235, showRate: 235 / 1745, salesRate: 85 / 235, buyingUnits: null, sold: 85, workshopAttendance: null },
  { team: 'Team Dent', market: 'Tulsa, OK', date: '2026-07-15', reg: 864, attended: 114, showRate: 114 / 864, salesRate: 20 / 114, buyingUnits: 20, sold: 20, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Nashville', date: '2026-07-11', reg: 923, attended: 114, showRate: 114 / 923, salesRate: 40 / 114, buyingUnits: null, sold: 40, workshopAttendance: null },
  { team: 'Team Dent', market: 'Oklahoma City', date: '2026-07-11', reg: 1302, attended: 130, showRate: 130 / 1302, salesRate: 32 / 130, buyingUnits: 29, sold: 32, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Long Island', date: '2026-07-11', reg: 1686, attended: 120, showRate: 120 / 1686, salesRate: 64 / 120, buyingUnits: null, sold: 64, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Phoenix', date: '2026-07-01', reg: 1022, attended: 111, showRate: 111 / 1022, salesRate: 36 / 111, buyingUnits: null, sold: 36, workshopAttendance: null },
  { team: 'Team Dent', market: 'Birmingham', date: '2026-06-30', reg: 1871, attended: 179, showRate: 179 / 1871, salesRate: 44 / 179, buyingUnits: 44, sold: 44, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Jacksonville', date: '2026-06-30', reg: 1433, attended: 136, showRate: 136 / 1433, salesRate: 57 / 136, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Seattle', date: '2026-06-23', reg: 1208, attended: 99, showRate: 99 / 1208, salesRate: 40 / 99, buyingUnits: null, sold: 40, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Columbus', date: '2026-06-23', reg: 1196, attended: 135, showRate: 135 / 1196, salesRate: 40 / 135, buyingUnits: null, sold: 40, workshopAttendance: null },
  { team: 'Team Dent', market: 'Orlando', date: '2026-06-23', reg: 1231, attended: 116, showRate: 116 / 1231, salesRate: 39 / 116, buyingUnits: 36, sold: 39, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Dallas', date: '2026-06-10', reg: 1634, attended: 174, showRate: 174 / 1634, salesRate: 60 / 174, buyingUnits: null, sold: 60, workshopAttendance: null },
  { team: 'Team Dent', market: 'Boston', date: '2026-06-10', reg: 1359, attended: 112, showRate: 112 / 1359, salesRate: 39 / 112, buyingUnits: null, sold: 39, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Charleston', date: '2026-06-09', reg: 1378, attended: 163, showRate: 163 / 1378, salesRate: 37 / 163, buyingUnits: 34, sold: 37, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Fort Myers', date: '2026-06-03', reg: 1098, attended: 172, showRate: 172 / 1098, salesRate: 54 / 172, buyingUnits: null, sold: 54, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Charlotte', date: '2026-06-03', reg: 1420, attended: 143, showRate: 143 / 1420, salesRate: 50 / 143, buyingUnits: 42, sold: 50, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Tampa', date: '2026-05-30', reg: 1641, attended: 139, showRate: 139 / 1641, salesRate: 51 / 139, buyingUnits: null, sold: 51, workshopAttendance: null },
  { team: 'Team Dent', market: 'RALEIGH', date: '2026-05-30', reg: 1215, attended: 155, showRate: 155 / 1215, salesRate: 38 / 155, buyingUnits: 34, sold: 38, workshopAttendance: null },
  { team: 'Team Vogel', market: 'WEST PALM BEACH', date: '2026-05-20', reg: 1723, attended: 176, showRate: 176 / 1723, salesRate: 65 / 176, buyingUnits: null, sold: 65, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Minneapolis', date: '2026-05-19', reg: 1382, attended: 158, showRate: 158 / 1382, salesRate: 51 / 158, buyingUnits: null, sold: 51, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Atlanta', date: '2026-05-06', reg: 2140, attended: 225, showRate: 225 / 2140, salesRate: 74 / 225, buyingUnits: null, sold: 74, workshopAttendance: null },
  { team: 'Team Dent', market: 'Norfolk', date: '2026-05-05', reg: 1450, attended: 177, showRate: 177 / 1450, salesRate: 55 / 177, buyingUnits: null, sold: 55, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Chicago', date: '2026-04-29', reg: 1583, attended: 216, showRate: 216 / 1583, salesRate: 67 / 216, buyingUnits: null, sold: 67, workshopAttendance: null },
  { team: 'Team Dent', market: 'RICHMOND, VA', date: '2026-04-28', reg: 1532, attended: 173, showRate: 173 / 1532, salesRate: 50 / 173, buyingUnits: null, sold: 50, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Los Angeles', date: '2026-04-22', reg: 1624, attended: 171, showRate: 171 / 1624, salesRate: 70 / 171, buyingUnits: null, sold: 70, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Los Angeles', date: '2026-04-15', reg: 1922, attended: 233, showRate: 233 / 1922, salesRate: 92 / 233, buyingUnits: null, sold: 92, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Phoenix', date: '2026-04-15', reg: 968, attended: 82, showRate: 82 / 968, salesRate: 31 / 82, buyingUnits: null, sold: 31, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Tucson', date: '2026-04-11', reg: 620, attended: 85, showRate: 85 / 620, salesRate: 29 / 85, buyingUnits: null, sold: 29, workshopAttendance: null },
  { team: 'Team Dent', market: 'Denver, CO', date: '2026-04-01', reg: 733, attended: 77, showRate: 77 / 733, salesRate: 24 / 77, buyingUnits: null, sold: 24, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Philadelphia', date: '2026-04-01', reg: 1549, attended: 156, showRate: 156 / 1549, salesRate: 64 / 156, buyingUnits: null, sold: 64, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Indianapolis', date: '2026-04-01', reg: 1029, attended: 112, showRate: 112 / 1029, salesRate: 50 / 112, buyingUnits: null, sold: 50, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Boston', date: '2026-03-25', reg: 947, attended: 113, showRate: 113 / 947, salesRate: 56 / 113, buyingUnits: null, sold: 56, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Orlando TDAI', date: '2026-03-24', reg: 1081, attended: 141, showRate: 141 / 1081, salesRate: 57 / 141, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Vogel', market: 'DC', date: '2026-03-11', reg: 1142, attended: 107, showRate: 107 / 1142, salesRate: 57 / 107, buyingUnits: null, sold: 57, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Dallas TDAI', date: '2026-03-11', reg: 1177, attended: 162, showRate: 162 / 1177, salesRate: 55 / 162, buyingUnits: null, sold: 55, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Memphis, TN', date: '2026-03-10', reg: 1661, attended: 297, showRate: 297 / 1661, salesRate: 67 / 297, buyingUnits: null, sold: 67, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Sacramento', date: '2026-03-04', reg: 1190, attended: 126, showRate: 126 / 1190, salesRate: 54 / 126, buyingUnits: null, sold: 54, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Hartford, CT', date: '2026-03-04', reg: 1363, attended: 201, showRate: 201 / 1363, salesRate: 79 / 201, buyingUnits: null, sold: 79, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Jacksonville TDAI', date: '2026-03-03', reg: 940, attended: 132, showRate: 132 / 940, salesRate: 33 / 132, buyingUnits: null, sold: 33, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Houston TDAI', date: '2026-02-25', reg: 1485, attended: 190, showRate: 190 / 1485, salesRate: 60 / 190, buyingUnits: null, sold: 60, workshopAttendance: null },
  { team: 'Team Dent', market: 'Orange County', date: '2026-02-24', reg: 1132, attended: 166, showRate: 166 / 1132, salesRate: 47 / 166, buyingUnits: null, sold: 47, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Portland, Oregon', date: '2026-02-24', reg: 823, attended: 136, showRate: 136 / 823, salesRate: 51 / 136, buyingUnits: null, sold: 51, workshopAttendance: null },
  { team: 'Team Wyman', market: 'San Diego', date: '2026-02-17', reg: 874, attended: 111, showRate: 111 / 874, salesRate: 32 / 111, buyingUnits: null, sold: 32, workshopAttendance: null },
  { team: 'Team Vogel', market: 'St Louis', date: '2026-02-17', reg: 1061, attended: 136, showRate: 136 / 1061, salesRate: 47 / 136, buyingUnits: null, sold: 47, workshopAttendance: null },
  { team: 'Team Dent', market: 'San Antonio, Texas', date: '2026-02-17', reg: 822, attended: 121, showRate: 121 / 822, salesRate: 30 / 121, buyingUnits: null, sold: 30, workshopAttendance: null },
  { team: 'Team Wyman', market: 'Las Vegas TDAI', date: '2026-02-11', reg: 1397, attended: 206, showRate: 206 / 1397, salesRate: 62 / 206, buyingUnits: null, sold: 62, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Hawaii', date: '2026-02-10', reg: 790, attended: 112, showRate: 112 / 790, salesRate: 29 / 112, buyingUnits: null, sold: 29, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Knoxville / Chattanooga, TN', date: '2026-02-10', reg: 1173, attended: 156, showRate: 156 / 1173, salesRate: 68 / 156, buyingUnits: null, sold: 68, workshopAttendance: null },
  { team: 'Team Vogel', market: 'San Francisco', date: '2026-01-28', reg: 1367, attended: 115, showRate: 115 / 1367, salesRate: 37 / 115, buyingUnits: null, sold: 37, workshopAttendance: null },
  { team: 'Team Wayne', market: 'West Palm Beach TDAI', date: '2026-01-28', reg: 981, attended: 151, showRate: 151 / 981, salesRate: 77 / 151, buyingUnits: null, sold: 77, workshopAttendance: null },
  { team: 'Team Wyman', market: 'GREENVILLE, SOUTH CAROLINA', date: '2026-01-28', reg: 405, attended: 60, showRate: 60 / 405, salesRate: 20 / 60, buyingUnits: null, sold: 20, workshopAttendance: null },
  { team: 'Team Wyman', market: 'NASHVILLE, TN', date: '2026-01-21', reg: 1081, attended: 171, showRate: 171 / 1081, salesRate: 52 / 171, buyingUnits: null, sold: 52, workshopAttendance: null },
  { team: 'Team Dent', market: 'Atlanta', date: '2026-01-21', reg: 1677, attended: 236, showRate: 236 / 1677, salesRate: 61 / 236, buyingUnits: null, sold: 61, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Washington DC TDAI', date: '2026-01-14', reg: 1353, attended: 205, showRate: 205 / 1353, salesRate: 76 / 205, buyingUnits: null, sold: 76, workshopAttendance: null },
  { team: 'Team Vogel', market: 'CHARLOTTE, N.C.', date: '2026-01-13', reg: 1295, attended: 194, showRate: 194 / 1295, salesRate: 63 / 194, buyingUnits: null, sold: 63, workshopAttendance: null },
  { team: 'Team Dent', market: 'Charleston', date: '2026-01-13', reg: 1397, attended: 203, showRate: 203 / 1397, salesRate: 60 / 203, buyingUnits: null, sold: 60, workshopAttendance: null },
  { team: 'Team Wayne', market: 'Fort Lauderdale TDAI', date: '2026-01-07', reg: 1349, attended: 216, showRate: 216 / 1349, salesRate: 88 / 216, buyingUnits: null, sold: 88, workshopAttendance: null },
  { team: 'Team Wyman', market: 'CHARLOTTE, N.C.', date: '2026-01-07', reg: 1217, attended: 220, showRate: 220 / 1217, salesRate: 65 / 220, buyingUnits: null, sold: 65, workshopAttendance: null },
  { team: 'Team Vogel', market: 'Santa Barbara', date: '2026-01-06', reg: 821, attended: 97, showRate: 97 / 821, salesRate: 36 / 97, buyingUnits: null, sold: 36, workshopAttendance: null }
];

export const currentMiddleEndWorkshops: MiddleEndCurrentWorkshop[] = [
  {
    market: 'Boise, ID', team: 'Team Nick · Speaker Nick', eventDate: '2026-08-23', buyingUnits: 30,
    soldClosed: 11, showed: 30, totalWritten: 203050, totalCollected: 186550,
    abcBreakdown: 'A: 4 buyers · 2 sold (50%) · B: 6 buyers · 4 sold (67%) · C: 20 buyers · 5 sold (25%)', notes: 'Final workshop post from #teamnick at 2026-08-23T15:22:03.029139-06:00: 30 BU, 11 total sales, $203,050 written, $186,550 collected.'
  },
  {
    market: 'Grand Rapids, MI', team: 'Team Tony · Speaker Tony', eventDate: '2026-08-23', buyingUnits: 33,
    soldClosed: 17, showed: 33, totalWritten: 354000, totalCollected: 326200,
    abcBreakdown: 'A: 2 buyers · 2 sold (100%) · B: 4 buyers · 3 sold (75%) · C: 27 buyers · 12 sold (52% as reported)', notes: 'Final workshop post from #teamtony at 2026-08-23T12:01:43.448659-06:00: 33 BU, 17 total sales, $354,000 written, $326,200 collected.'
  },
  {
    market: 'Chicago, IL', team: 'Team Tony · Speaker Tony', eventDate: '2026-08-16', buyingUnits: 51,
    soldClosed: 22, showed: 51, totalWritten: 269500, totalCollected: 134450,
    abcBreakdown: 'A: 6 buyers · 3 sold (50%) · B: 7 buyers · 3 sold (43%) · C: 34 buyers · 15 sold (44%)', notes: 'Final workshop post from #teamtony at 2026-08-16T15:16:22.263729-06:00: 51 BU, 22 total sales, $269,500 written, $134,450 collected.'
  },
  {
    market: 'Denver, CO', team: 'Team Drecksel · Speaker Drecksel', eventDate: '2026-08-16', buyingUnits: 26,
    soldClosed: 11, showed: 26, totalWritten: 200650, totalCollected: 156650,
    abcBreakdown: 'A: 3 buyers · 2 sold (67%) · B: 4 buyers · 2 sold (50%) · C: 19 buyers · 7 sold (37%)', notes: 'Final workshop post from #teamdrecksel at 2026-08-16T15:08:01.834289-06:00: 26 BU, 11 total sales, $200,650 written, $156,650 collected.'
  },
  {
    market: 'Indianapolis, IN', team: 'Team Shaw · Speaker Shaw', eventDate: '2026-08-16', buyingUnits: 43,
    soldClosed: 18, showed: 43, totalWritten: 218500, totalCollected: 213000,
    abcBreakdown: 'A: 3 buyers · 1 sold (33%) · B: 6 buyers · 4 sold (67%) · C: 34 buyers · 13 sold (38%)', notes: 'Final workshop post from #teamshaw at 2026-08-16T12:57:35.495989-06:00: 43 BU, 18 total sales, $218,500 written, $213,000 collected.'
  },
  {
    market: 'Hartford, CT', team: 'Team Tony · Speaker Tony', eventDate: '2026-08-02', buyingUnits: 52,
    soldClosed: 23, showed: 52, totalWritten: 377500, totalCollected: 356100,
    abcBreakdown: 'A: 8 buyers · 4 sold (50%) · B: 4 buyers · 1 sold (25%) · C: 37 buyers · 17 sold (46%)', notes: 'Final workshop post from #teamtony at 2026-08-02T15:41:44.332939-06:00: 52 BU, 23 total sales, $377,500 written, $356,100 collected.'
  },
  {
    market: 'Memphis, TN', team: 'Team Drecksel · Speaker Drecksel', eventDate: '2026-08-02', buyingUnits: 77,
    soldClosed: 24, showed: 77, totalWritten: 331000, totalCollected: 200500,
    abcBreakdown: 'A: 7 buyers · 4 sold (57%) · B: 8 buyers · 4 sold (50%) · C: 57 buyers · 16 sold (26% as reported)', notes: 'Final workshop post from #teamdrecksel at 2026-08-02T14:39:02.893979-06:00: 77 BU, 24 total sales, $331,000 written, $200,500 collected.'
  },
  {
    market: 'Tulsa Oklahoma', team: 'Team Nick · Speaker Nick', eventDate: '2026-08-02', buyingUnits: 16,
    soldClosed: 7, showed: 16, totalWritten: 109700, totalCollected: 73700,
    abcBreakdown: 'A: 2 sold · B: 0 sold · C: 5 sold', notes: 'Final workshop post from #teamnick at 2026-08-02T12:41:53.961089-06:00: 16 BU, 7 total sales, $109,700 written, $73,700 collected.'
  }
];

export const middleEndHistory: MiddleEndHistoricalRow[] = [
  { team: 'Team Tony', market: 'Norfolk', date: '2026-05-21', buyingUnits: 42, soldClosed: 26, totalWritten: 371750, totalCollected: 241250, abcBreakdown: 'A: 5/7 = 71% · B: 3/6 = 50% · C: 20/31 = 65%', otherStats: 'PIF 14 ($176,000), Penders 2, CR 12, remaining CR collections $104,500, personal-funds balance $26,000, Avvance 0, JumpStart 7, Cancels 3/42 = 7%.' },
  { team: 'Team Tony', market: 'Long Island', date: '2026-05-07', buyingUnits: 63, soldClosed: 26, totalWritten: 312500, totalCollected: 229750, abcBreakdown: 'A: 6/10 = 60% · B: 0/1 = 0% · C: 20/54 = 37%', otherStats: 'PIF 21, Penders 3, CR 4, Avvance 3, JumpStart 12, Cancels 3/63 = 4%.' },
  { team: 'Team Tony', market: 'LA2', date: '2026-05-01', buyingUnits: 28, soldClosed: 11, totalWritten: 142500, totalCollected: 74800, abcBreakdown: 'A: 1/3 = 33% · B: 0/2 = 0% · C: 10/23 = 43%', otherStats: 'PIF 7, Penders 2, CR 2, JumpStart 4, Cancels 4/28 = 14%.' },
  { team: 'Team Tony', market: 'Tucson', date: '2026-04-24', buyingUnits: 30, soldClosed: 15, totalWritten: 303000, totalCollected: 210000, abcBreakdown: 'A: 4/5 = 80% · B: 0/1 = 0% · C: 11/24 = 46%', otherStats: 'PIF 8, Penders 4, CR 2, Avvance 2, JumpStart 4, Cancels 2/30 = 7%.' },
  { team: 'Team Tony', market: 'Indianapolis', date: '2026-04-17', buyingUnits: 45, soldClosed: 14, totalWritten: 213000, totalCollected: 119286.57, abcBreakdown: 'A: 2/3 = 67% · B: 2/6 = 33% · C: 7/36 = 20%', otherStats: 'PIF 9, Penders 1, Avvance 2, JumpStart 6, Cancels 1/45 = 2%.' },
  { team: 'Team Tony', market: 'Hartford', date: '2026-03-20', buyingUnits: 61, soldClosed: 23, totalWritten: 388500, totalCollected: 219500, abcBreakdown: 'A: 7/8 = 88% · B: 2/3 = 67% · C: 14/53 = 26%', otherStats: 'PIF 11, Penders 2, CR 11, Avvance 2, Cancels 2/61 = 3%.' },
  { team: 'Team Tony', market: 'St. Louis', date: '2026-03-06', buyingUnits: 41, soldClosed: 20, totalWritten: 258000, totalCollected: 167500, abcBreakdown: 'A: 2/3 = 67% · B: 1/2 = 50% · C: 17/36 = 50%', otherStats: 'PIF 16, Penders 1, CR 7, Avvance 1, Cancels 3/41 = 13%.' },
  { team: 'Team Tony', market: 'Greenville', date: '2026-02-13', buyingUnits: 24, soldClosed: 8, totalWritten: 171500, totalCollected: 64000, abcBreakdown: 'A: 2/5 = 40% · B: 3/5 = 60% · C: 3/14 = 21%', otherStats: 'PIF 2, Penders 1, CR 6, Cancels 0/24 = 0%.' },
  { team: 'Team Tony', market: 'Charlotte', date: '2026-02-06', buyingUnits: 48, soldClosed: 22, totalWritten: 425000, totalCollected: 159800, abcBreakdown: 'A: 4/5 = 80% · B: 3/3 = 100% · C: 15/42 = 36%', otherStats: 'PIF 5, Penders 3, CR 17, Avvance 2, Cancels 0/48 = 0%.' },
  { team: 'Team Tony', market: 'Burbank', date: '2026-01-16', buyingUnits: 9, soldClosed: 5, totalWritten: 99800, totalCollected: 89300, abcBreakdown: 'A: 1/1 = 100% · B: 2/2 = 100% · C: 2/6 = 33%', otherStats: 'PIF 4, Penders 1, CR 4, Cancels 1/9 = 11%.' },

  { team: 'Team Nick', market: 'Chicago', date: '2026-05-15', buyingUnits: 52, soldClosed: 14, totalWritten: 152000, totalCollected: 122000, abcBreakdown: 'A: 1/4 = 25% · B: 3/5 = 60% · C: 10/49 = 20%', otherStats: 'PIF 12, Penders 3, CR 2, Avvance 1, JumpStart 7, Cancels 4/52 = 7.6%.' },
  { team: 'Team Drexel', market: 'Richmond', date: '2026-05-15', buyingUnits: 44, soldClosed: 17, totalWritten: 265500, totalCollected: 173200, abcBreakdown: 'A: 5/12 = 42% · B: 1/3 = 33% · C: 11/29 = 38%', otherStats: 'PIF 10, Penders 0, CR 6, Avvance 3, JumpStart 6, 4 Diamonds, Cancels 2%.' },
  { team: 'Team Drexel', market: 'Fort Lauderdale', date: '2026-05-07', buyingUnits: 58, soldClosed: 19, totalWritten: 284000, totalCollected: 198500, abcBreakdown: 'A: 6/10 = 60% · B: 4/7 = 57% · C: 9/41 = 22%', otherStats: 'PIF 14, Penders 1, CR 10, JumpStart 8, Cancels 2%, 120% of goal hit.' },
  { team: 'Team Drexel', market: 'LA1', date: '2026-04-24', buyingUnits: 40, soldClosed: 7, totalWritten: 82500, totalCollected: 48000, abcBreakdown: 'A: 1/4 = 25% · B: 0 = 0% · C: 5/32 = 16%', otherStats: 'PIF 4, Penders 1, CR 0, JumpStart 3, Cancels 5/40 = 12.5%.' },
  { team: 'Team Drexel', market: 'Boston', date: '2026-04-10', buyingUnits: 50, soldClosed: 19, totalWritten: 284500, totalCollected: 176100, abcBreakdown: 'A: 4/9 = 44% · B: 4/7 = 57% · C: 9/32 = 28%', otherStats: 'PIF 12, CR 8, JumpStart 7, Cancels 3/50 = 6%.' },
  { team: 'Team Drexel', market: 'DC', date: '2026-03-27', buyingUnits: 50, soldClosed: 17, totalWritten: 187500, totalCollected: 151000, abcBreakdown: 'A: 4/5 = 80% · B: 1/5 = 20% · C: 12/40 = 30%', otherStats: 'PIF 13, Penders 3, CR 6, JumpStart 9, Cancels 3/50 = 6%.' },
  { team: 'Team Drexel', market: 'Sacramento', date: '2026-03-20', buyingUnits: 41, soldClosed: 15, totalWritten: 258500, totalCollected: 90400, abcBreakdown: 'A: 2/6 = 33% · B: 3/4 = 75% · C: 10/31 = 32%', otherStats: 'PIF 6, CR 7, Avvance 1, JumpStart 2, Cancels 4/41 = 9%.' },
  { team: 'Team Drexel', market: 'Portland', date: '2026-03-13', buyingUnits: 37, soldClosed: 14, totalWritten: 264500, totalCollected: 172100, abcBreakdown: 'A: 5/10 = 50% · B: 2/4 = 50% · C: 7/23 = 30%', otherStats: 'PIF 9, Penders 2, CR 6, Avvance 1, JumpStart 5, Cancels 2/37 = 5%.' },
  { team: 'Team Drexel', market: 'San Diego', date: '2026-03-06', buyingUnits: 29, soldClosed: 8, totalWritten: 136500, totalCollected: 88200, abcBreakdown: 'A: 2/7 = 29% · B: 2/3 = 67% · C: 4/19 = 21%', otherStats: 'PIF 4, Penders 1, CR 4, JumpStart 1, Cancels 0/29 = 0%.' },
  { team: 'Team Drexel', market: 'Las Vegas', date: '2026-02-27', buyingUnits: 57, soldClosed: 12, totalWritten: 170500, totalCollected: 116500, abcBreakdown: 'A: 5/9 = 56% · B: 0/2 = 0% · C: 7/42 = 17%', otherStats: 'PIF 9, CR 4, JumpStart 4, Cancels 4/57 = 7%.' },
  { team: 'Team Drexel', market: 'San Francisco', date: '2026-02-13', buyingUnits: 28, soldClosed: 6, totalWritten: 86500, totalCollected: 59600, abcBreakdown: 'A: 1/1 = 100% · B: 3/6 = 50% · C: 2/21 = 10%', otherStats: 'PIF 4, Penders 2, CR 3, Cancels 3/28 = 10.7%.' },
  { team: 'Team Drexel', market: 'Atlanta', date: '2026-02-06', buyingUnits: 51, soldClosed: 16, totalWritten: 242000, totalCollected: 135400, abcBreakdown: 'A: 3/8 = 38% · B: 3/6 = 50% · C: 8/37 = 22%', otherStats: 'PIF 7, Penders 1, CR 6, Avvance 3, JumpStart 4, Cancels 2/51 = 3.9%.' },
  { team: 'Team Drexel', market: 'Fort Lauderdale (TDAI)', date: '2026-01-23', buyingUnits: 76, soldClosed: 19, totalWritten: 247500, totalCollected: 157700, abcBreakdown: 'A: 1/7 = 14% · B: 1/4 = 25% · C: 17/65 = 26%', otherStats: 'PIF 14, Penders 5, CR 2, Avvance 4, JumpStart 8, Cancels 2/76 = 3%.' },
  { team: 'Team Drexel', market: 'Orlando', date: '2026-01-16', buyingUnits: 33, soldClosed: 6, totalWritten: 125500, totalCollected: 89000, abcBreakdown: 'A: 1/3 = 33% · B: 1/2 = 50% · C: 4/28 = 14%', otherStats: 'PIF 4, Penders 3, CR 4, Avvance 2, Cancels 2/33 = 6%.' },
  { team: 'Team Drexel', market: 'Austin', date: '2026-01-09', buyingUnits: 34, soldClosed: 12, totalWritten: 226000, totalCollected: 166000, abcBreakdown: null, otherStats: 'PIF 7, one Avvance-approved PIF after event.' },

  { team: 'Team Shaw', market: 'Atlanta', date: '2026-05-21', buyingUnits: 61, soldClosed: 20, totalWritten: 246000, totalCollected: 124755, abcBreakdown: 'A: 4/10 = 40% · B: 0/4 = 0% · C: 16/47 = 34%', otherStats: 'Updated final: PIF 9 ($71,500), Penders 1, CR 6, remaining CR collections $72,545, personal-funds balance $48,700, Avvance 1, JumpStart 11, Diamonds 4, Cancels 5/61 = 8%.' },
  { team: 'Team Shaw', market: 'Phoenix', date: '2026-05-01', buyingUnits: 22, soldClosed: 10, totalWritten: 97500, totalCollected: 59750, abcBreakdown: 'A: 2/5 = 40% · B: 0 = 0% · C: 9/22 = 41%', otherStats: 'PIF 6, Penders 2, CR 1, Avvance 1, JumpStart 4, Cancels 2/22 = 9%.' },
  { team: 'Team Shaw', market: 'Philadelphia', date: '2026-04-17', buyingUnits: 48, soldClosed: 16, totalWritten: 206250, totalCollected: 150750, abcBreakdown: 'A: 1/6 = 17% · B: 0/1 = 0% · C: 15/41 = 37%', otherStats: 'PIF 9, Penders 3, CR 5, Avvance 2, JumpStart 6, Cancels 4/48 = 8%.' },
  { team: 'Team Shaw', market: 'Baltimore', date: '2026-04-10', buyingUnits: 59, soldClosed: 24, totalWritten: 288000, totalCollected: 234000, abcBreakdown: 'A: 4/11 = 36% · B: 3/8 = 38% · C: 17/40 = 43%', otherStats: 'PIF 12, Penders 1, CR 10, Avvance 6, JumpStart 8, Cancels 2/59 = 3%.' },
  { team: 'Team Shaw', market: 'Dallas', date: '2026-03-27', buyingUnits: 57, soldClosed: 20, totalWritten: 261000, totalCollected: 152750, abcBreakdown: 'A: 7/12 = 58% · B: 1/4 = 25% · C: 12/41 = 29%', otherStats: 'PIF 12, Penders 3, CR 10, JumpStart 7, Cancels 1/57 = 2%.' },
  { team: 'Team Shaw', market: 'Jacksonville', date: '2026-03-20', buyingUnits: 29, soldClosed: 9, totalWritten: 83500, totalCollected: 45000, abcBreakdown: 'A: 0/0 = N/A · B: 1/4 = 25% · C: 8/25 = 32%', otherStats: 'PIF 6, Penders 2, CR 5, Avvance 1, JumpStart 5, Cancels 1/29 = 3%.' },
  { team: 'Team Shaw', market: 'Orange County', date: '2026-03-13', buyingUnits: 37, soldClosed: 17, totalWritten: 247500, totalCollected: 171500, abcBreakdown: 'A: 5/6 = 83% · B: 6/9 = 67% · C: 6/22 = 27%', otherStats: 'PIF 9, Penders 3, CR 11, Avvance 2, JumpStart 5.5.' },
  { team: 'Team Shaw', market: 'Honolulu', date: '2026-02-27', buyingUnits: 17, soldClosed: 9, totalWritten: 137000, totalCollected: 96500, abcBreakdown: 'A: 2/5 = 40% · B: 0 = 0% · C: 7/12 = 58%', otherStats: 'PIF 7, Penders 1, CR 2, Avvance 3, JumpStart 3, Cancels 2/17 = 12%.' },
  { team: 'Team Shaw', market: 'West Palm Beach', date: '2026-02-13', buyingUnits: 52, soldClosed: 11, totalWritten: 153000, totalCollected: 140500, abcBreakdown: 'A: 3/10 = 30% · B: 1/5 = 20% · C: 7/38 = 18%', otherStats: 'PIF 10, Penders 4, CR 5, Avvance 1, JumpStart 5, Cancels 2/52 = 4%.' },
  { team: 'Team Shaw', market: 'Washington DC #2', date: '2026-02-06', buyingUnits: 37, soldClosed: 14, totalWritten: 318500, totalCollected: 273000, abcBreakdown: 'A: 6/11 = 55% · B: 1/3 = 33% · C: 7/23 = 30%', otherStats: 'PIF 12, Penders 1, CR 6, Avvance 5, JumpStart 1, Cancels 2/37 = 5%.' },
  { team: 'Team Shaw', market: 'Washington DC #1', date: '2026-01-30', buyingUnits: 27, soldClosed: 12, totalWritten: 217500, totalCollected: 159000, abcBreakdown: 'A: 3/7 = 43% · B: 1/4 = 25% · C: 8/16 = 50%', otherStats: 'PIF 9, Penders 1, CR 5, Avvance 4, JumpStart 3, Cancels 3/27 = 11%.' },
  { team: 'Team Shaw', market: 'Thousand Oaks', date: '2026-01-23', buyingUnits: 28, soldClosed: 8, totalWritten: 100000, totalCollected: 77000, abcBreakdown: 'A: 2/7 = 29% · B: 1/4 = 25% · C: 5/17 = 29%', otherStats: 'PIF 6, Penders 4, CR 0, Avvance 2, JumpStart 4, Cancels 1/28 = 3%.' },
  { team: 'Team Shaw', market: 'Dallas wksp 1', date: '2026-01-09', buyingUnits: 42, soldClosed: 14, totalWritten: 262500, totalCollected: 188000, abcBreakdown: 'A: 4/5 = 80% · B: 1/5 = 20% · C: 9/32 = 33%', otherStats: 'PIF 8, Penders 4, CR 2, Avvance 5, Cancels 3/42 = 7%.' },

  { team: 'Team Nick', market: 'Denver', date: '2026-04-17', buyingUnits: 19, soldClosed: 4, totalWritten: 58500, totalCollected: 53200, abcBreakdown: 'A: 2/5 = 40% · B: 1/1 = 100% · C: 1/13 = 8%', otherStats: 'PIF 2, Penders 1, CR 2, JumpStart 2, Cancels 2/19 = 11%.' },
  { team: 'Team Nick', market: 'Orlando', date: '2026-04-10', buyingUnits: 50, soldClosed: 11, totalWritten: 167000, totalCollected: 85500, abcBreakdown: 'A: 2/10 = 20% · B: 2/2 = 100% · C: 7/41 = 17%', otherStats: 'PIF 6, Penders 5, CR 2, JumpStart 3, Cancels 4/50 = 8%.' },
  { team: 'Team Nick', market: 'Memphis', date: '2026-03-27', buyingUnits: 54, soldClosed: 13, totalWritten: 210500, totalCollected: 157000, abcBreakdown: 'A: 3/6 = 50% · B: 1/2 = 50% · C: 9/46 = 20%', otherStats: 'PIF 9, Penders 1, CR 4, Avvance 1, JumpStart 4, Cancels 8/54 = 15%.' },
  { team: 'Team Nick', market: 'Houston', date: '2026-03-13', buyingUnits: 44, soldClosed: 12, totalWritten: 116500, totalCollected: 83100, abcBreakdown: 'A: 3/7 = 43% · B: 0/2 = 0% · C: 8/35 = 23%', otherStats: 'PIF 9, CR 4, JumpStart 9, Cancels 4/44 = 9%.' },
  { team: 'Team Nick', market: 'San Antonio', date: '2026-03-06', buyingUnits: 28, soldClosed: 8, totalWritten: 84000, totalCollected: 49000, abcBreakdown: 'A: 1/3 = 33% · B: 0/3 = 0% · C: 7/22 = 32%', otherStats: 'PIF 4, CR 6, JumpStart 3, Cancels 4/28 = 14%.' },
  { team: 'Team Nick', market: 'Knoxville', date: '2026-02-27', buyingUnits: 59, soldClosed: 12, totalWritten: 174000, totalCollected: 171000, abcBreakdown: 'A: 1/6 = 17% · B: 3/6 = 50% · C: 8/37 = 22%', otherStats: 'PIF 11, Penders 5, CR 7, JumpStart 3, Cancels 4/59 = 6%.' },
  { team: 'Team Nick', market: 'Raleigh', date: '2026-02-13', buyingUnits: 40, soldClosed: 18, totalWritten: 194000, totalCollected: 145500, abcBreakdown: 'A: 4/6 = 67% · B: 1/2 = 50% · C: 13/31 = 42%', otherStats: 'PIF 14, Penders 4, CR 5, Avvance 1, JumpStart 9, Cancels 2/40 = 5%.' },
  { team: 'Team Nick', market: 'Nashville', date: '2026-02-06', buyingUnits: 39, soldClosed: 13, totalWritten: 156000, totalCollected: 118500, abcBreakdown: 'A: 3/4 = 75% · B: 2/3 = 67% · C: 8/31 = 26%', otherStats: 'PIF 10, Penders 1, CR 5, Avvance 1, JumpStart 5, Cancels 2/39 = 5%.' },
  { team: 'Team Nick', market: 'Charleston', date: '2026-01-30', buyingUnits: 54, soldClosed: 15, totalWritten: 219000, totalCollected: 142950, abcBreakdown: null, otherStats: 'PIF 10, Penders 1, CR 5, Avvance 3, JumpStart 6.' },
];

export const insideSalesSourceCategories: InsideSalesSourceRow[] = [
  { source: 'BB - PIF', leads: 479, revenue: 3222246.0, dpl: 6727, revenueShare: 0.5490937730465026 },
  { source: 'UTL Upsell', leads: 1144, revenue: 1554000.0, dpl: 1358, revenueShare: 0.264812718617469 },
  { source: 'Jumpstart', leads: 375, revenue: 366147.0, dpl: 976, revenueShare: 0.062394068522284706 },
  { source: 'ANB', leads: 2019, revenue: 359767.22000000003, dpl: 178, revenueShare: 0.06130690836399555 },
  { source: 'BB - Collections', leads: 92, revenue: 202282.98, dpl: 2199, revenueShare: 0.03447046709385014 },
  { source: 'BB - Canceled', leads: 13, revenue: 99855.0, dpl: 7681, revenueShare: 0.01701600644629818 },
  { source: 'Pender', leads: 166, revenue: 42000.0, dpl: 253, revenueShare: 0.007157100503174838 },
  { source: 'RNA', leads: 2, revenue: 18000.0, dpl: 9000, revenueShare: 0.0030673287870749306 },
  { source: 'Expo Collections', leads: 1, revenue: 4000.0, dpl: 4000, revenueShare: 0.0006816286193499846 },
  { source: 'BB - Recontracted', leads: 1, revenue: 0.0, dpl: 0, revenueShare: 0.0 },
  { source: 'Buyer', leads: 1, revenue: 0.0, dpl: 0, revenueShare: 0.0 },
  { source: 'expo buyer', leads: 10, revenue: 0.0, dpl: 0, revenueShare: 0.0 },
  { source: 'Low Buyer', leads: 12, revenue: 0.0, dpl: 0, revenueShare: 0.0 }
];

export const insideSalesRepRows: InsideSalesRepRow[] = [
  { rep: 'Tyler M', leads: 205, revenue: 914000.0, dpl: 4459.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Travis R', leads: 1, revenue: 4000.0, dpl: 4000.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Hyatt', leads: 273, revenue: 1073721.0, dpl: 3933.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Cory', leads: 406, revenue: 1311299.98, dpl: 3230.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Steven K', leads: 286, revenue: 818489.0, dpl: 2862.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Nick Helf', leads: 112, revenue: 261500.0, dpl: 2335.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'CD Manager', leads: 36, revenue: 57000.0, dpl: 1583.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Ryan I', leads: 461, revenue: 593200.0, dpl: 1287.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Dagan', leads: 1, revenue: 1000.0, dpl: 1000.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Derek Merrill', leads: 63, revenue: 62800.0, dpl: 997.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Brett Dean', leads: 67, revenue: 64500.0, dpl: 963.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Bryan S', leads: 347, revenue: 296700.0, dpl: 855.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Carson M', leads: 157, revenue: 55000.0, dpl: 350.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Greg A', leads: 1107, revenue: 269212.9, dpl: 243.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Larry L', leads: 789, revenue: 85875.32, dpl: 109.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' },
  { rep: 'Chris Hall', leads: 4, revenue: 0.0, dpl: 0.0, collected: null, collectedDpl: null, source: 'Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched 2026-08-29T14:06:39.701Z' }
];

export const speakerCollectionRows: SpeakerCollectionRow[] = [
  { speaker: 'Tony', amountIntoCollections: 1707013.43, collectionsOut: 601788.4299999999, pendingOutstanding: 110416.075329, sixWeekCollected: 178325, tenWeekCollected: 280075, dplOrCollectionMetric: 'YTD collections performance · fetched 2026-08-29T06:04:55.955799-06:00' },
  { speaker: 'Jazey', amountIntoCollections: 1564450, collectionsOut: 1034100, pendingOutstanding: 82626.7458, sixWeekCollected: 199500, tenWeekCollected: 250500, dplOrCollectionMetric: 'YTD collections performance · fetched 2026-08-29T06:04:55.955799-06:00' },
  { speaker: 'Megan', amountIntoCollections: 944820, collectionsOut: 438835, pendingOutstanding: 83016.834532, sixWeekCollected: 33400, tenWeekCollected: 65525, dplOrCollectionMetric: 'YTD collections performance · fetched 2026-08-29T06:04:55.955799-06:00' },
  { speaker: 'Nick', amountIntoCollections: 844850, collectionsOut: 499350, pendingOutstanding: 64812.01022699999, sixWeekCollected: 72950, tenWeekCollected: 152450, dplOrCollectionMetric: 'YTD collections performance · fetched 2026-08-29T06:04:55.955799-06:00' },
  { speaker: 'Nate', amountIntoCollections: 107500, collectionsOut: 21000, pendingOutstanding: 6187.5, sixWeekCollected: null, tenWeekCollected: null, dplOrCollectionMetric: 'YTD collections performance · fetched 2026-08-29T06:04:55.955799-06:00' }
];
