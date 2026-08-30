import { triggerRefreshWorkflow } from "./_lib/githubDispatch.js";
import { json, methodNotAllowed, serviceUnavailable, unauthorized } from "./_lib/http.js";
import { isRefreshConflict, readRefreshState, writeRefreshState } from "./_lib/refreshState.js";
import { isTeamAuthenticated } from "./_lib/security.js";

const ACTIVE = new Set(["queued", "running"]);
const COOLDOWN_MS = 2 * 60 * 1000;

export async function POST(request: Request): Promise<Response> {
  if (request.method !== "POST") return methodNotAllowed(["POST"]);
  if (!await isTeamAuthenticated(request)) return unauthorized("Basic");

  try {
    const { state, etag } = await readRefreshState();
    if (ACTIVE.has(state.status)) return json({ accepted: true, existing: true, refresh: state }, 202);
    if (state.requested_at && Date.now() - Date.parse(state.requested_at) < COOLDOWN_MS) {
      return json({ error: "refresh_cooldown", retry_after_seconds: 120, refresh: state }, 429, { "retry-after": "120" });
    }
    const now = new Date().toISOString();
    const queued = {
      ...state,
      status: "queued" as const,
      request_id: crypto.randomUUID(),
      requested_at: now,
      started_at: null,
      completed_at: null,
      requested_by: "team" as const,
      message: "Refresh queued. The Studio worker starts within five minutes.",
    };
    await writeRefreshState(queued, etag);
    try {
      await triggerRefreshWorkflow(queued.request_id);
    } catch {
      // Best-effort: the request is already queued in the gist, so the Studio
      // worker (or the next scheduled Action) still services it if dispatch fails.
    }
    return json({ accepted: true, existing: false, refresh: queued }, 202);
  } catch (error) {
    if (isRefreshConflict(error)) return json({ error: "refresh_conflict", retry: true }, 409);
    const reason = error instanceof Error ? error.message.slice(0, 160) : "refresh_queue_unavailable";
    return serviceUnavailable(reason);
  }
}