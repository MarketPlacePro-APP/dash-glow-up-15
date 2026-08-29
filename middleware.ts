import { next } from "@vercel/functions";
import {
  hasAccountingConfiguration,
  hasTeamConfiguration,
  hasWorkerConfiguration,
  isAccountingAuthenticated,
  isTeamAuthenticated,
  isWorkerAuthenticated,
} from "./api/_lib/security.js";

const securityHeaders = (pathname: string): HeadersInit => ({
  "cache-control": pathname.startsWith("/assets/")
    ? "private, max-age=300, must-revalidate"
    : "private, no-store",
  "content-security-policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  vary: "Authorization",
});

const denied = (pathname: string, scheme: "Basic" | "Bearer", configured: boolean): Response => new Response(
  pathname.startsWith("/api/")
    ? JSON.stringify({ error: configured ? "unauthorized" : "authentication_not_configured" })
    : "Authentication required.",
  {
    status: configured ? 401 : 503,
    headers: {
      ...securityHeaders(pathname),
      "content-type": pathname.startsWith("/api/") ? "application/json; charset=utf-8" : "text/plain; charset=utf-8",
      ...(configured ? { "www-authenticate": scheme === "Basic" ? 'Basic realm="TLWB KPI", charset="UTF-8"' : 'Bearer realm="TLWB KPI API"' } : {}),
    },
  },
);

export default async function middleware(request: Request): Promise<Response> {
  const pathname = new URL(request.url).pathname;

  if (pathname.startsWith("/api/internal/")) {
    if (!await isWorkerAuthenticated(request)) return denied(pathname, "Bearer", hasWorkerConfiguration());
  } else if (pathname.startsWith("/api/v1/")) {
    if (!await isAccountingAuthenticated(request)) return denied(pathname, "Bearer", hasAccountingConfiguration() || hasTeamConfiguration());
  } else if (!await isTeamAuthenticated(request)) {
    return denied(pathname, "Basic", hasTeamConfiguration());
  }

  return next({ headers: securityHeaders(pathname) });
}

export const config = { matcher: "/(.*)" };