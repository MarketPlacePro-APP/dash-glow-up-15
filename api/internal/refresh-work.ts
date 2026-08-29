import { json, methodNotAllowed, serviceUnavailable, unauthorized } from "../_lib/http.js";
import { isRefreshConflict, readRefreshState, writeRefreshState } from "../_lib/refreshState.js";
import { isWorkerAuthenticated } from "../_lib/security.js";

type WorkerAction = "start" | "requeue" | "complete" | "no_change" | "fail" | "scheduled_result";

async function handler(request: Request): Promise<Response> {
  if (!await isWorkerAuthenticated(request)) return unauthorized("Bearer");
  if (request.method === "GET") {
    try {
      const { state } = await readRefreshState();
      return json({ refresh: state });
    } catch {
      return serviceUnavailable("refresh_queue_unavailable");
    }
  }
  if (request.method !== "POST") return methodNotAllowed(["GET", "POST"]);

  try {
    const rawBody = typeof (request as Request & { json?: () => Promise<unknown> }).json === "function"
      ? await (request as Request).json()
      : (request as Request & { body?: unknown }).body;
    const body = (typeof rawBody === "string" ? JSON.parse(rawBody) : rawBody ?? {}) as {
      action?: WorkerAction;
      request_id?: string;
      message?: string;
      completed_at?: string;
      published_at?: string | null;
      deployed_fingerprint?: string | null;
      result?: "deployed" | "no_change" | "failed";
    };
    const { state, etag } = await readRefreshState();
    const now = body.completed_at ?? new Date().toISOString();

    if (body.action === "scheduled_result") {
      const result = body.result ?? "failed";
      const next = {
        ...state,
        last_check_completed_at: now,
        last_check_result: result,
        last_published_at: body.published_at ?? state.last_published_at,
        deployed_fingerprint: body.deployed_fingerprint ?? state.deployed_fingerprint,
      };
      await writeRefreshState(next, etag);
      return json({ refresh: next });
    }

    if (!body.request_id || body.request_id !== state.request_id) return json({ error: "request_id_mismatch", refresh: state }, 409);
    let next = state;
    if (body.action === "start" && state.status === "queued") {
      next = { ...state, status: "running", started_at: now, message: body.message ?? "Source collection and validation are running." };
    } else if (body.action === "requeue" && state.status === "running") {
      next = { ...state, status: "queued", started_at: null, message: body.message ?? "The owner pipeline is busy; this request will retry." };
    } else if (body.action === "complete" && state.status === "running") {
      next = { ...state, status: "succeeded", completed_at: now, message: body.message ?? "New source data was published and verified.", last_check_completed_at: now, last_check_result: "deployed", last_published_at: body.published_at ?? now, deployed_fingerprint: body.deployed_fingerprint ?? state.deployed_fingerprint };
    } else if (body.action === "no_change" && state.status === "running") {
      next = { ...state, status: "no_change", completed_at: now, message: body.message ?? "Checked all sources; no material data changed.", last_check_completed_at: now, last_check_result: "no_change", deployed_fingerprint: body.deployed_fingerprint ?? state.deployed_fingerprint };
    } else if (body.action === "fail" && state.status === "running") {
      next = { ...state, status: "failed", completed_at: now, message: body.message ?? "Refresh failed closed; the prior verified build remains live.", last_check_completed_at: now, last_check_result: "failed" };
    } else {
      return json({ error: "invalid_transition", action: body.action, refresh: state }, 409);
    }

    await writeRefreshState(next, etag);
    return json({ refresh: next });
  } catch (error) {
    if (isRefreshConflict(error)) return json({ error: "refresh_conflict", retry: true }, 409);
    return serviceUnavailable("refresh_queue_unavailable");
  }
}

export const GET = handler;
export const POST = handler;
