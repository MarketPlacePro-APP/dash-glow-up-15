import statusArtifact from "./_data/status.generated.js";
import { json, methodNotAllowed, unauthorized } from "./_lib/http.js";
import { defaultRefreshState, publicRefreshState, readRefreshState } from "./_lib/refreshState.js";
import { isTeamAuthenticated } from "./_lib/security.js";

const nextScheduledCheck = (now = new Date()): string => {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Denver",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit",
    hour12: false,
  });
  const parts = Object.fromEntries(formatter.formatToParts(now).filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
  const mountainNow = new Date(`${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}`);
  const candidate = new Date(mountainNow);
  candidate.setSeconds(0, 0);
  if (candidate.getMinutes() >= 5) candidate.setHours(candidate.getHours() + 1);
  candidate.setMinutes(5);
  if (candidate.getHours() > 22) {
    candidate.setDate(candidate.getDate() + 1);
    candidate.setHours(8, 5, 0, 0);
  } else if (candidate.getHours() < 8) {
    candidate.setHours(8, 5, 0, 0);
  }
  const offsetFormatter = new Intl.DateTimeFormat("en-US", { timeZone: "America/Denver", timeZoneName: "longOffset" });
  const offset = offsetFormatter.formatToParts(now).find((part) => part.type === "timeZoneName")?.value.replace("GMT", "") || "-06:00";
  return `${candidate.getFullYear()}-${String(candidate.getMonth() + 1).padStart(2, "0")}-${String(candidate.getDate()).padStart(2, "0")}T${String(candidate.getHours()).padStart(2, "0")}:${String(candidate.getMinutes()).padStart(2, "0")}:00${offset}`;
};

export async function GET(request: Request): Promise<Response> {
  if (request.method !== "GET") return methodNotAllowed(["GET"]);
  if (!await isTeamAuthenticated(request)) return unauthorized("Basic");
  try {
    const { state } = await readRefreshState();
    return json({
      ...statusArtifact,
      last_checked: state.last_check_completed_at ?? statusArtifact.last_checked,
      last_published: state.last_published_at ?? statusArtifact.last_published,
      next_scheduled_check: nextScheduledCheck(),
      queue_configured: Boolean(process.env.TLWB_REFRESH_GIST_ID && process.env.TLWB_REFRESH_GIST_TOKEN),
      refresh: publicRefreshState(state),
    });
  } catch {
    return json({
      ...statusArtifact,
      next_scheduled_check: nextScheduledCheck(),
      refresh: publicRefreshState(defaultRefreshState()),
    });
  }
}