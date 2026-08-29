const DEFAULT_REPO = "MarketPlacePro-APP/dash-glow-up-15";
const REFRESH_EVENT_TYPE = "tlwb-kpi-refresh";

export const hasDispatchConfiguration = (): boolean => Boolean(process.env.TLWB_DISPATCH_TOKEN);

/**
 * Fire a GitHub repository_dispatch so the "Refresh now" button can trigger the
 * off-Studio GitHub Actions refresh directly, instead of only queuing a gist
 * request the Studio worker must poll. Inert until TLWB_DISPATCH_TOKEN is set, so
 * this stays dormant through Phase 1 and activates at Phase 2 cutover.
 */
export const triggerRefreshWorkflow = async (requestId: string | null): Promise<boolean> => {
  const token = process.env.TLWB_DISPATCH_TOKEN?.trim();
  if (!token) return false;
  const repo = process.env.TLWB_DISPATCH_REPO?.trim() || DEFAULT_REPO;
  const response = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
    method: "POST",
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${token}`,
      "x-github-api-version": "2022-11-28",
      "content-type": "application/json",
      "user-agent": "tlwb-kpi-refresh-control",
    },
    body: JSON.stringify({
      event_type: REFRESH_EVENT_TYPE,
      client_payload: { request_id: requestId },
    }),
  });
  if (!response.ok) {
    const detail = (await response.text()).replace(/\s+/g, " ").slice(0, 80);
    throw new Error(`dispatch_${response.status}:${detail}`);
  }
  return true;
};
