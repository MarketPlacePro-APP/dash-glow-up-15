import type {
  AnalyticsBrainAggregate,
  AnalyticsBrainDataset,
  AnalyticsBrainDecisionStatus,
  AnalyticsBrainDimension,
  AnalyticsBrainDimensionQa,
  AnalyticsBrainEventState,
  AnalyticsBrainMetricRow,
  AnalyticsBrainSourceMeta,
} from "@/types";
import generatedArtifact from "./analyticsBrain.generated.json";

type RawRow = Record<string, string>;

type GeneratedArtifact = {
  version: number;
  batchToken: string;
  decisionStatus: AnalyticsBrainDecisionStatus;
  source: AnalyticsBrainSourceMeta;
  reports: Record<string, string | string[]>;
  files: Record<string, string>;
  batchFiles: string[];
  rows: Record<"eventSummary" | "channels" | "campaigns" | "adSets" | "ads", RawRow[]>;
  qa: {
    requiredDimensionsPresent: boolean;
    optionalAdNamePresent: boolean;
    sameBatch: boolean;
    sourceSnapshotProvided: boolean;
    dimensions: Record<string, AnalyticsBrainDimensionQa>;
    reconciliation: Record<string, { values: Record<string, number>; spread: number; tolerance: number; withinTolerance: boolean }>;
    reconciliationPassed: boolean;
    numericParseErrors: Array<Record<string, string | number>>;
    impossibleRatios: Array<Record<string, string | number>>;
    zeroBlankRule: string;
    smallSampleThreshold: number;
  };
};

const rawArtifact = generatedArtifact as unknown as GeneratedArtifact;

const MONTHS: Record<string, string> = {
  Jan: "01", Feb: "02", Mar: "03", Apr: "04", May: "05", Jun: "06",
  Jul: "07", Aug: "08", Sep: "09", Oct: "10", Nov: "11", Dec: "12",
};

export function parseAnalyticsNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  if (!text || ["-", "—", "n/a", "na", "null", "none"].includes(text.toLowerCase())) return null;
  const negative = text.startsWith("(") && text.endsWith(")");
  const cleaned = text.replace(/[$,%]/g, "").replace(/[()]/g, "").trim();
  const parsed = Number(cleaned);
  if (!Number.isFinite(parsed)) return null;
  return negative ? -parsed : parsed;
}

export function parseAnalyticsPercent(value: unknown): number | null {
  const parsed = parseAnalyticsNumber(value);
  if (parsed === null) return null;
  return String(value).includes("%") ? parsed / 100 : parsed;
}

export function parseAnalyticsMarketDate(value: unknown): string | null {
  const match = String(value ?? "").trim().match(/^([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})$/);
  if (!match || !MONTHS[match[1]]) return null;
  return `${match[3]}-${MONTHS[match[1]]}-${match[2].padStart(2, "0")}`;
}

export function ratio(numerator: number | null, denominator: number | null): number | null {
  if (numerator === null || denominator === null || denominator === 0) return null;
  return numerator / denominator;
}

export function eventState(
  marketDate: string | null,
  attended: number | null,
  exportedAt: string,
): AnalyticsBrainEventState {
  if (!marketDate) return "incomplete";
  const exportDate = exportedAt.slice(0, 10);
  if (marketDate > exportDate) return "upcoming";
  if (marketDate === exportDate && (attended ?? 0) === 0) return "incomplete";
  return "completed";
}

export function isSmallSample(registrations: number | null, threshold = 100): boolean {
  return registrations !== null && registrations < threshold;
}

export function isZeroCost(spend: number | null): boolean {
  return spend === 0;
}

const rowConfig: Record<
  Exclude<AnalyticsBrainDimension, "event">,
  { key: string; reportKey: string; fileKey: string }
> = {
  channel: { key: "Channel", reportKey: "channels", fileKey: "channels" },
  campaign: { key: "Campaign", reportKey: "campaigns", fileKey: "campaigns" },
  adSet: { key: "Ad Set", reportKey: "adSets", fileKey: "adSets" },
  ad: { key: "Ad Name", reportKey: "ads", fileKey: "ads" },
};

function normalizeEvent(row: RawRow): AnalyticsBrainMetricRow {
  const spend = parseAnalyticsNumber(row.Spend);
  const registrations = parseAnalyticsNumber(row.Registrations);
  const attended = parseAnalyticsNumber(row.Attendance);
  const buyers = parseAnalyticsNumber(row.Buyers);
  const netFeRevenue = parseAnalyticsNumber(row["Net FE Revenue"]);
  const netMeRevenue = parseAnalyticsNumber(row["Net ME Revenue"]);
  const marketDate = parseAnalyticsMarketDate(row["Market Date"]);
  const sourceShowRate = parseAnalyticsPercent(row["Show Rate"]);
  const sourceFeRom = parseAnalyticsNumber(row["FE ROM"]);
  const sourceFeMeRom = parseAnalyticsNumber(row["FE+ME ROM"]);
  return {
    id: `event:${row["Market Group"] || row["Market Name"]}`,
    dimension: "event",
    channel: "All channels",
    name: row["Market Name"] || "Unlabeled market",
    marketDate,
    marketGroup: row["Market Group"] || null,
    spend,
    registrations,
    guests: parseAnalyticsNumber(row.Guests),
    attended,
    buyers,
    netFeRevenue,
    grossMeRevenue: parseAnalyticsNumber(row["Gross ME Revenue"]),
    netMeRevenue,
    sourceShowRate,
    sourceBuyRate: ratio(buyers, attended),
    sourceFeRom,
    sourceFeMeRom,
    derivedShowRate: ratio(attended, registrations),
    derivedBuyRate: ratio(buyers, attended),
    derivedCostPerRegistration: ratio(spend, registrations),
    derivedCostPerAttendee: ratio(spend, attended),
    derivedCostPerBuyer: ratio(spend, buyers),
    derivedFeRom: ratio(netFeRevenue, spend),
    derivedFeMeRom: ratio((netFeRevenue ?? 0) + (netMeRevenue ?? 0), spend),
    eventState: eventState(marketDate, attended, rawArtifact.source.exportedAt),
    smallSample: isSmallSample(registrations, rawArtifact.qa.smallSampleThreshold),
    zeroCost: isZeroCost(spend),
    anomaly: sourceShowRate !== null && sourceShowRate > 1 ? "Source show rate exceeds 100%; review attribution grain." : null,
    reportName: String(rawArtifact.reports.eventSummary),
    filename: rawArtifact.files.eventSummary,
    batchToken: rawArtifact.batchToken,
    raw: row,
  };
}

function normalizePerformance(row: RawRow, dimension: Exclude<AnalyticsBrainDimension, "event">): AnalyticsBrainMetricRow {
  const config = rowConfig[dimension];
  const spend = parseAnalyticsNumber(row["Total Cost"]);
  const registrations = parseAnalyticsNumber(row.Registrations);
  const attended = parseAnalyticsNumber(row.Attended);
  const buyers = parseAnalyticsNumber(row.Buyers);
  const netFeRevenue = parseAnalyticsNumber(row["Net FE Revenue"]);
  const netMeRevenue = parseAnalyticsNumber(row["Net ME Revenue"]);
  const sourceShowRate = parseAnalyticsPercent(row["Show Rate"]);
  const sourceBuyRate = parseAnalyticsPercent(row["Buy Rate"]);
  const name = row[config.key] || "Unlabeled row";
  const anomaly = sourceShowRate !== null && sourceShowRate > 1
    ? "Source show rate exceeds 100%; attended attribution exceeds registrations."
    : null;
  return {
    id: `${dimension}:${row.Channel || "unknown"}:${name}`,
    dimension,
    channel: row.Channel || "Unknown",
    name,
    marketDate: null,
    marketGroup: null,
    spend,
    registrations,
    guests: null,
    attended,
    buyers,
    netFeRevenue,
    grossMeRevenue: parseAnalyticsNumber(row["Gross ME Revenue"]),
    netMeRevenue,
    sourceShowRate,
    sourceBuyRate,
    sourceFeRom: parseAnalyticsNumber(row["FE ROM"]),
    sourceFeMeRom: parseAnalyticsNumber(row["FE+ME ROM"]),
    derivedShowRate: ratio(attended, registrations),
    derivedBuyRate: ratio(buyers, attended),
    derivedCostPerRegistration: ratio(spend, registrations),
    derivedCostPerAttendee: ratio(spend, attended),
    derivedCostPerBuyer: ratio(spend, buyers),
    derivedFeRom: ratio(netFeRevenue, spend),
    derivedFeMeRom: ratio((netFeRevenue ?? 0) + (netMeRevenue ?? 0), spend),
    eventState: null,
    smallSample: isSmallSample(registrations, rawArtifact.qa.smallSampleThreshold),
    zeroCost: isZeroCost(spend),
    anomaly,
    reportName: String(rawArtifact.reports[config.reportKey]),
    filename: rawArtifact.files[config.fileKey],
    batchToken: rawArtifact.batchToken,
    raw: row,
  };
}

export function weightedAggregate(rows: AnalyticsBrainMetricRow[]): AnalyticsBrainAggregate {
  const sum = (pick: (row: AnalyticsBrainMetricRow) => number | null) =>
    rows.reduce((total, row) => total + (pick(row) ?? 0), 0);
  const spend = sum((row) => row.spend);
  const registrations = sum((row) => row.registrations);
  const attended = sum((row) => row.attended);
  const guests = sum((row) => row.guests);
  const buyers = sum((row) => row.buyers);
  const netFeRevenue = sum((row) => row.netFeRevenue);
  const grossMeRevenue = sum((row) => row.grossMeRevenue);
  const netMeRevenue = sum((row) => row.netMeRevenue);
  return {
    spend,
    registrations,
    attended,
    guests,
    buyers,
    netFeRevenue,
    grossMeRevenue,
    netMeRevenue,
    showRate: ratio(attended, registrations),
    buyRate: ratio(buyers, attended),
    costPerRegistration: ratio(spend, registrations),
    costPerAttendee: ratio(spend, attended),
    costPerBuyer: ratio(spend, buyers),
    feRom: ratio(netFeRevenue, spend),
    feMeRom: ratio(netFeRevenue + netMeRevenue, spend),
  };
}

export function assertAnalyticsBrainBatch(input: {
  batchToken: string;
  requiredDimensionsPresent: boolean;
  sameBatch: boolean;
  campaigns: AnalyticsBrainMetricRow[];
  adSets: AnalyticsBrainMetricRow[];
  ads?: AnalyticsBrainMetricRow[];
}): void {
  if (!input.requiredDimensionsPresent || !input.campaigns.length || !input.adSets.length) {
    throw new Error("Analytics Brain required Campaign and Ad Set dimensions are missing");
  }
  if (!input.sameBatch) throw new Error("Analytics Brain export batch is inconsistent");
  const rows = [...input.campaigns, ...input.adSets, ...(input.ads ?? [])];
  if (rows.some((row) => row.batchToken !== input.batchToken)) {
    throw new Error("Analytics Brain dimensions cannot be mixed across batch tokens");
  }
}

const eventSummary = rawArtifact.rows.eventSummary.map(normalizeEvent);
const channels = rawArtifact.rows.channels.map((row) => normalizePerformance(row, "channel"));
const campaigns = rawArtifact.rows.campaigns.map((row) => normalizePerformance(row, "campaign"));
const adSets = rawArtifact.rows.adSets.map((row) => normalizePerformance(row, "adSet"));
const ads = rawArtifact.rows.ads.map((row) => normalizePerformance(row, "ad"));

assertAnalyticsBrainBatch({
  batchToken: rawArtifact.batchToken,
  requiredDimensionsPresent: rawArtifact.qa.requiredDimensionsPresent,
  sameBatch: rawArtifact.qa.sameBatch,
  campaigns,
  adSets,
  ads,
});

export const analyticsBrain: AnalyticsBrainDataset = {
  version: rawArtifact.version,
  batchToken: rawArtifact.batchToken,
  decisionStatus: rawArtifact.decisionStatus,
  source: rawArtifact.source,
  reports: rawArtifact.reports,
  files: rawArtifact.files,
  batchFiles: rawArtifact.batchFiles,
  eventSummary,
  channels,
  campaigns,
  adSets,
  ads,
  executive: weightedAggregate(eventSummary),
  qa: rawArtifact.qa,
};
