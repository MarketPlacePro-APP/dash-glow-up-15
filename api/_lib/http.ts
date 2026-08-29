export const json = (body: unknown, status = 200, extraHeaders: HeadersInit = {}): Response => new Response(
  JSON.stringify(body, null, 2),
  {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "private, no-store",
      "x-content-type-options": "nosniff",
      vary: "Authorization",
      ...extraHeaders,
    },
  },
);

export const methodNotAllowed = (allowed: string[]): Response => json(
  { error: "method_not_allowed", allowed },
  405,
  { allow: allowed.join(", ") },
);

export const unauthorized = (scheme: "Basic" | "Bearer" = "Bearer"): Response => json(
  { error: "unauthorized" },
  401,
  { "www-authenticate": scheme === "Basic" ? 'Basic realm="TLWB KPI", charset="UTF-8"' : 'Bearer realm="TLWB KPI API"' },
);

export const serviceUnavailable = (reason: string): Response => json(
  { error: "service_unavailable", reason },
  503,
);