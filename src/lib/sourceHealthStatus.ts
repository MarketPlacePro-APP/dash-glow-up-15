import type { SourceHealthStatus } from "@/types";

export type CheckOutcome = "ok_fresh" | "ok_no_new_expected" | "failed" | "not_in_channel";

export function computeSourceHealthStatus({
  checkOutcome,
  scheduleState,
  latestSourcePostDate,
  lastChecked,
  expectedHours,
  now,
}: {
  checkOutcome: CheckOutcome;
  scheduleState: string;
  latestSourcePostDate: string | null;
  lastChecked: string | null;
  expectedHours: number;
  now: Date;
}): SourceHealthStatus {
  if (checkOutcome === "failed") return "red";
  if (checkOutcome === "not_in_channel") return "yellow";
  if (!lastChecked) return "red";
  if (scheduleState === "completed" || scheduleState === "historical") return "neutral/fine";
  if (!latestSourcePostDate) return "yellow";

  const latest = Date.parse(latestSourcePostDate);
  if (!Number.isFinite(latest)) return "yellow";
  const ageHours = (now.getTime() - latest) / 3_600_000;
  if (checkOutcome === "ok_no_new_expected" && (scheduleState === "upcoming" || scheduleState === "completed")) {
    return "neutral/fine";
  }
  return ageHours <= expectedHours ? "green" : "yellow";
}
