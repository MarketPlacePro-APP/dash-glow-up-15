import statusArtifact from "../_data/status.generated.js";
import { json, methodNotAllowed, unauthorized } from "../_lib/http.js";
import { publicRefreshState, readRefreshState } from "../_lib/refreshState.js";
import { isAccountingAuthenticated } from "../_lib/security.js";

export async function GET(request: Request): Promise<Response> {
  if (request.method !== "GET") return methodNotAllowed(["GET"]);
  if (!await isAccountingAuthenticated(request)) return unauthorized("Bearer");
  const { state } = await readRefreshState();
  return json({ ...statusArtifact, refresh: publicRefreshState(state) });
}