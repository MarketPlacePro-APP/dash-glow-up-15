import { describe, expect, it } from "vitest";
import phase2aAuditData from "../../data/phase2a_audit.json";
import sourceHealthData from "../../data/source_health.json";
import scheduleData from "../../data/schedule.json";
import type { Phase2AAuditArtifact, SourceHealthArtifact } from "@/types";
import { computeSourceHealthStatus } from "@/lib/sourceHealthStatus";
import { activePreviewMarkets, expoCounts } from "@/data/executiveAdapters";

const sourceHealth = sourceHealthData as SourceHealthArtifact;
const phase2aAudit = phase2aAuditData as Phase2AAuditArtifact;

describe("Phase 1 freshness spine", () => {
  it("maps every rendered section health row to at least one source and check timestamp", () => {
    expect(sourceHealth.rows.length).toBeGreaterThan(0);
    for (const row of sourceHealth.rows) {
      expect(row.sources.length, `${row.page} / ${row.section}`).toBeGreaterThan(0);
      expect(row.last_checked, `${row.page} / ${row.section}`).toMatch(/^20\d{2}-\d{2}-\d{2}T/);
    }
  });

  it("requires all Phase 1 Slack channels and keeps optional not_in_channel coverage non-blocking", () => {
    expect(sourceHealth.required_channels).toEqual([
      "teamdrecksel",
      "teamtony",
      "teamnick",
      "teamshaw",
      "teamwayne",
      "teamdent",
      "teamwyman",
      "teamvogel",
      "teammillar",
      "eventstats",
      "expo",
    ]);
    expect(sourceHealth.channel_aliases.teamvogal).toBe("teamvogel");
    for (const channel of sourceHealth.optional_channels) {
      const row = sourceHealth.rows.find((item) => item.section === `Optional coverage: #${channel}`);
      expect(row, channel).toBeDefined();
      expect(row?.status, channel).not.toBe("red");
      expect(row?.expected_cadence, channel).toBe("not blocking");
      expect(row?.notes, channel).toMatch(/non-blocking|does not block/i);
      if (row?.status === "green") {
        expect(row.latest_source_post_date, channel).toBeTruthy();
        expect(row.notes, channel).toMatch(/live-readable/i);
      } else {
        expect(row?.status, channel).toBe("yellow");
        expect(row?.notes, channel).toMatch(/not_in_channel/i);
      }
    }
  });

  it("does not allow March-dated active source data to render green", () => {
    const status = computeSourceHealthStatus({
      checkOutcome: "ok_fresh",
      scheduleState: "current",
      latestSourcePostDate: "2026-03-15T12:00:00-06:00",
      lastChecked: "2026-06-21T12:00:00-06:00",
      expectedHours: 24,
      now: new Date("2026-06-21T18:00:00-06:00"),
    });
    expect(status).not.toBe("green");
    expect(["yellow", "red"]).toContain(status);
  });

  it("renders current/upcoming route blocks first and does not mark completed routes pending", () => {
    const blocks = scheduleData.route_blocks as Array<{ status: string; startDate: string; market: string; team: string }>;
    const firstCurrentOrUpcoming = blocks.findIndex((block) => block.status === "active" || block.status === "upcoming");
    const lastCurrentOrUpcoming = blocks.map((block) => block.status === "active" || block.status === "upcoming").lastIndexOf(true);
    expect(firstCurrentOrUpcoming).toBeGreaterThanOrEqual(0);
    expect(blocks.slice(firstCurrentOrUpcoming, lastCurrentOrUpcoming + 1).every((block) => block.status === "active" || block.status === "upcoming")).toBe(true);
    expect(blocks.filter((block) => block.status === "historical").some((block) => block.status === "upcoming")).toBe(false);
  });

  it("surfaces confirmed Megan coverage through Team Shaw", () => {
    const row = sourceHealth.rows.find((item) => item.section === "Coverage requirement: Megan");
    expect(row?.status).toBe("green");
    expect(row?.sources).toContain("slack:#teamshaw");
    expect(row?.notes).toMatch(/Megan confirmed as Team Shaw/i);
  });

  it("parses the current Expo standalone TLWB count instead of flyout text", () => {
    const values = Object.fromEntries(expoCounts.map((item) => [item.label, item.value]));
    expect(values.BU).toBeTypeOf("number");
    expect(values.Guests).toBeTypeOf("number");
    expect(values.Total).toBe((values.BU ?? 0) + (values.Guests ?? 0));
    expect(values.UTL).toBeTypeOf("number");
    expect(values.TLWB).toBeTypeOf("number");
    expect(values.KeySpire).toBeTypeOf("number");
  });

  it("keeps latest preview rows first and requires live rows only during active routes", () => {
    const datedPreviewMarkets = activePreviewMarkets.filter((item) => item.sourcePostedAt);
    expect(datedPreviewMarkets.length).toBeGreaterThan(0);

    const latestPreviewDate = datedPreviewMarkets
      .map((item) => item.sourcePostedAt?.slice(0, 10) ?? "")
      .sort()
      .at(-1);

    const latestPreviewMarkets = activePreviewMarkets.filter((item) => item.sourcePostedAt?.startsWith(latestPreviewDate ?? ""));
    const liveMarkets = latestPreviewMarkets.filter((item) => item.sourceState === "active_session");
    const finalMarkets = latestPreviewMarkets.filter((item) => item.sourceState === "final_route_totals");
    const pendingMarkets = latestPreviewMarkets.filter((item) => item.sourceState === "pending_source");
    const hasActivePreviewRoute =
      (scheduleData.records as Array<{ state?: string; eventType?: string }>).some(
        (record) => record.state === "active" && record.eventType === "front_end_preview",
      ) ||
      (scheduleData.route_blocks as Array<{ status: string; route?: string; id?: string; sourceRole?: string }>).some(
        (block) =>
          block.status === "active" &&
          [block.route, block.id, block.sourceRole].some((value) => String(value ?? "").toLowerCase().includes("preview")),
      );

    expect(latestPreviewMarkets.length).toBeGreaterThanOrEqual(1);
    expect(liveMarkets.length + finalMarkets.length + pendingMarkets.length).toBe(latestPreviewMarkets.length);
    if (hasActivePreviewRoute) {
      expect(liveMarkets.length + pendingMarkets.length).toBeGreaterThanOrEqual(1);
    } else {
      expect(finalMarkets.length + pendingMarkets.length).toBeGreaterThanOrEqual(1);
    }

    for (const market of pendingMarkets) {
      expect(market.status).toBe("yellow");
      expect(market.registered).toBeGreaterThan(0);
      expect(market.sessionsCompleted).toBeNull();
      expect(market.totalSessions).toBeNull();
      expect(market.attendedCutoff).toBe(0);
      expect(market.sales).toBe(0);
    }

    const firstOlderIndex = activePreviewMarkets.findIndex((item) => item.sourcePostedAt?.slice(0, 10) !== latestPreviewDate);
    if (firstOlderIndex >= 0) {
      expect(activePreviewMarkets.slice(0, firstOlderIndex).every((item) => item.sourcePostedAt?.startsWith(latestPreviewDate ?? ""))).toBe(true);
    }
    for (const market of liveMarkets) {
      expect(market.status).toBe("green");
      expect(market.sessionsCompleted).not.toBeNull();
      expect(market.totalSessions).not.toBeNull();
      expect(market.sessionsCompleted ?? 0).toBeLessThanOrEqual(market.totalSessions ?? 0);
      expect(market.routeDeals ?? market.sales).toBeGreaterThanOrEqual(market.sales);
      expect(market.salesRate).toBeCloseTo((market.routeDeals ?? market.sales) / market.attendedCutoff, 2);
    }
  });

  it("ships Phase 2A normalized audit rows for high-risk cards", () => {
    expect(phase2aAudit.phase).toBe("2A");
    expect(phase2aAudit.counts.event_roster).toBeGreaterThanOrEqual(6);
    expect(phase2aAudit.counts.metric_rows).toBeGreaterThanOrEqual(18);
    expect(phase2aAudit.acceptance.required_sections_present).toBe(true);
    expect(phase2aAudit.acceptance.high_risk_cards_from_normalized_records).toBe(true);
    expect(phase2aAudit.acceptance.stale_or_missing_sources_fail_closed).toBe(true);
    expect(phase2aAudit.event_roster.some((event) => event.event_id.startsWith("preview_"))).toBe(true);
    expect(phase2aAudit.event_roster.some((event) => event.event_id.startsWith("middle_end_"))).toBe(true);
  });
});
