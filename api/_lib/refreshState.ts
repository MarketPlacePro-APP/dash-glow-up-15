export type RefreshStatus = "idle" | "queued" | "running" | "succeeded" | "no_change" | "failed";

export type RefreshState = {
  schema_version: 1;
  status: RefreshStatus;
  request_id: string | null;
  requested_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  requested_by: "team" | null;
  message: string;
  last_check_completed_at: string | null;
  last_check_result: "deployed" | "no_change" | "failed" | null;
  last_published_at: string | null;
  deployed_fingerprint: string | null;
};

export const REFRESH_STATE_FILENAME = "tlwb-kpi-refresh-control.json";

export class RefreshConflictError extends Error {
  constructor() {
    super("refresh_conflict");
    this.name = "RefreshConflictError";
  }
}

export const defaultRefreshState = (): RefreshState => ({
  schema_version: 1,
  status: "idle",
  request_id: null,
  requested_at: null,
  started_at: null,
  completed_at: null,
  requested_by: null,
  message: "Ready for the next scheduled or requested source check.",
  last_check_completed_at: null,
  last_check_result: null,
  last_published_at: null,
  deployed_fingerprint: null,
});

const gistConfig = (): { id: string; token: string } | null => {
  const id = process.env.TLWB_REFRESH_GIST_ID?.trim();
  const token = process.env.TLWB_REFRESH_GIST_TOKEN?.trim();
  if (!id || !token) return null;
  return { id, token };
};

const gistHeaders = (token: string, extra: HeadersInit = {}): HeadersInit => ({
  accept: "application/vnd.github+json",
  authorization: `Bearer ${token}`,
  "x-github-api-version": "2022-11-28",
  "user-agent": "tlwb-kpi-refresh-control",
  ...extra,
});

export const readRefreshState = async (): Promise<{ state: RefreshState; etag: string | null }> => {
  const config = gistConfig();
  if (!config) return { state: defaultRefreshState(), etag: null };
  try {
    const response = await fetch(`https://api.github.com/gists/${config.id}`, {
      headers: gistHeaders(config.token),
      cache: "no-store",
    });
    if (response.status === 404) return { state: defaultRefreshState(), etag: null };
    if (!response.ok) throw new Error(`gist_read_${response.status}`);
    const body = await response.json() as {
      files?: Record<string, { content?: string | null } | undefined>;
    };
    const text = body.files?.[REFRESH_STATE_FILENAME]?.content;
    const etag = response.headers.get("etag");
    if (!text) return { state: defaultRefreshState(), etag };
    return { state: { ...defaultRefreshState(), ...JSON.parse(text) } as RefreshState, etag };
  } catch {
    return { state: defaultRefreshState(), etag: null };
  }
};

export const writeRefreshState = async (state: RefreshState, etag: string | null): Promise<RefreshState> => {
  const config = gistConfig();
  if (!config) throw new Error("refresh_queue_unavailable");
  const response = await fetch(`https://api.github.com/gists/${config.id}`, {
    method: "PATCH",
    headers: gistHeaders(config.token, { "content-type": "application/json" }),
    body: JSON.stringify({
      files: {
        [REFRESH_STATE_FILENAME]: { content: JSON.stringify(state, null, 2) },
      },
    }),
  });
  if (response.status === 412 || response.status === 409) throw new RefreshConflictError();
  if (!response.ok) {
    const detail = (await response.text()).replace(/\s+/g, " ").slice(0, 80);
    throw new Error(`gist_write_${response.status}:${detail}`);
  }
  return state;
};

export const isRefreshConflict = (error: unknown): boolean => error instanceof RefreshConflictError;

export const publicRefreshState = (state: RefreshState) => ({
  status: state.status,
  request_id: state.request_id,
  requested_at: state.requested_at,
  started_at: state.started_at,
  completed_at: state.completed_at,
  message: state.message,
  last_check_completed_at: state.last_check_completed_at,
  last_check_result: state.last_check_result,
  last_published_at: state.last_published_at,
});
