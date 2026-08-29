export type SourceCheckOutcome =
  | "ok_fresh"
  | "ok_stale"
  | "degraded"
  | "missing"
  | "error"
  | (string & {});

export type SourceScheduleState =
  | "current"
  | "active"
  | "upcoming"
  | "historical"
  | "idle"
  | (string & {});

export type SourceHealthStatus = "green" | "yellow" | "red";

export interface SourceHealthInput {
  checkOutcome: SourceCheckOutcome;
  scheduleState: SourceScheduleState;
  latestSourcePostDate?: string | null;
  lastChecked?: string | null;
  expectedHours: number;
  now?: Date;
}

const HOUR_MS = 3_600_000;

const parseTimestamp = (value?: string | null): number | null => {
  if (!value) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const requiresLiveFreshness = (state: SourceScheduleState): boolean =>
  state === "current" || state === "active";

/**
 * Grade a dashboard source's health from the freshness of its newest real data
 * post, not from when the automated check last ran. Active markets must show
 * data within their expected cadence to read green; stale-but-checked sources
 * degrade to yellow, and missing/failed checks or absent posts read red.
 */
export function computeSourceHealthStatus(input: SourceHealthInput): SourceHealthStatus {
  const now = (input.now ?? new Date()).getTime();
  const expectedHours = input.expectedHours > 0 ? input.expectedHours : 24;

  if (input.checkOutcome === "error" || input.checkOutcome === "missing") {
    return "red";
  }

  const postedAt = parseTimestamp(input.latestSourcePostDate);
  const needsFresh = requiresLiveFreshness(input.scheduleState);

  if (postedAt === null) {
    return needsFresh ? "red" : "yellow";
  }

  if (!needsFresh) {
    return input.checkOutcome === "ok_fresh" ? "green" : "yellow";
  }

  const ageHours = (now - postedAt) / HOUR_MS;
  if (input.checkOutcome === "ok_fresh" && ageHours <= expectedHours) {
    return "green";
  }
  if (ageHours <= expectedHours * 2) {
    return "yellow";
  }
  return "red";
}
