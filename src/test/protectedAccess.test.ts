import { afterEach, beforeEach, describe, expect, it } from "vitest";
import middleware from "../../middleware";
import accounting from "../../api/_data/accounting.generated";
import status from "../../api/_data/status.generated";
import {
  isAccountingAuthenticated,
  isTeamAuthenticated,
  isWorkerAuthenticated,
  safeEqual,
} from "../../api/_lib/security";

const basic = (username: string, password: string) => `Basic ${Buffer.from(`${username}:${password}`).toString("base64")}`;

const original = {
  username: process.env.TLWB_AUTH_USERNAME,
  password: process.env.TLWB_AUTH_PASSWORD,
  worker: process.env.TLWB_WORKER_TOKEN,
  accounting: process.env.TLWB_DAVID_API_TOKEN,
};

beforeEach(() => {
  process.env.TLWB_AUTH_USERNAME = "tlwb-team";
  process.env.TLWB_AUTH_PASSWORD = "test-team-password";
  process.env.TLWB_WORKER_TOKEN = "test-worker-token";
  process.env.TLWB_DAVID_API_TOKEN = "test-accounting-token";
});

afterEach(() => {
  for (const [key, value] of Object.entries(original)) {
    const environmentKey = {
      username: "TLWB_AUTH_USERNAME",
      password: "TLWB_AUTH_PASSWORD",
      worker: "TLWB_WORKER_TOKEN",
      accounting: "TLWB_DAVID_API_TOKEN",
    }[key] as string;
    if (value === undefined) delete process.env[environmentKey];
    else process.env[environmentKey] = value;
  }
});

describe("protected dashboard access", () => {
  it("uses digest comparison and rejects changed values", async () => {
    await expect(safeEqual("same", "same")).resolves.toBe(true);
    await expect(safeEqual("same", "different")).resolves.toBe(false);
  });

  it("accepts only the configured shared Basic credentials", async () => {
    const good = new Request("https://tlwb-kpi.test/", { headers: { authorization: basic("tlwb-team", "test-team-password") } });
    const bad = new Request("https://tlwb-kpi.test/", { headers: { authorization: basic("tlwb-team", "wrong") } });
    await expect(isTeamAuthenticated(good)).resolves.toBe(true);
    await expect(isTeamAuthenticated(bad)).resolves.toBe(false);
    await expect(isTeamAuthenticated({ headers: { authorization: basic("tlwb-team", "test-team-password") } })).resolves.toBe(true);
  });

  it("keeps worker and accounting bearer credentials scoped separately", async () => {
    const worker = new Request("https://tlwb-kpi.test/api/internal/refresh-work", { headers: { authorization: "Bearer test-worker-token" } });
    const david = new Request("https://tlwb-kpi.test/api/v1/accounting/summary", { headers: { authorization: "Bearer test-accounting-token" } });
    await expect(isWorkerAuthenticated(worker)).resolves.toBe(true);
    await expect(isAccountingAuthenticated(worker)).resolves.toBe(false);
    await expect(isAccountingAuthenticated(david)).resolves.toBe(true);
    await expect(isWorkerAuthenticated(david)).resolves.toBe(false);
  });

  it("denies anonymous HTML and static assets before delivery", async () => {
    for (const pathname of ["/", "/preview", "/assets/index.js", "/favicon.ico"]) {
      const response = await middleware(new Request(`https://tlwb-kpi.test${pathname}`));
      expect(response.status, pathname).toBe(401);
      expect(response.headers.get("www-authenticate"), pathname).toContain("Basic");
      expect(response.headers.get("cache-control"), pathname).toContain("private");
    }
  });

  it("fails closed when shared credentials are not configured", async () => {
    delete process.env.TLWB_AUTH_USERNAME;
    delete process.env.TLWB_AUTH_PASSWORD;
    const response = await middleware(new Request("https://tlwb-kpi.test/"));
    expect(response.status).toBe(503);
    expect(response.headers.get("www-authenticate")).toBeNull();
  });
});

describe("generated protected payloads", () => {
  it("contains an explicit freshness contract", () => {
    expect(status.schema_version).toBe(1);
    expect(status.refresh_schedule).toBe("5 8-22 * * *");
    expect(status.last_checked).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it("exposes only bounded accounting resources", () => {
    expect(accounting.schema_version).toBe(1);
    expect(accounting.summary.current_workshop_count).toBe(accounting.events.length);
    expect(accounting.collections.length).toBeGreaterThan(0);
    expect(accounting.inside_sales.representatives.length).toBeGreaterThan(0);
    expect(Object.keys(accounting).sort()).toEqual([
      "collections",
      "events",
      "freshness",
      "generated_at",
      "inside_sales",
      "schema_version",
      "source_as_of",
      "summary",
    ]);
  });
});
