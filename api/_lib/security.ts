const encoder = new TextEncoder();

type RequestLike = { headers: Headers | Record<string, string | string[] | undefined> };

const requestHeader = (request: RequestLike, name: string): string | null => {
  const headers = request.headers as Headers & Record<string, string | string[] | undefined>;
  if (typeof headers.get === "function") return headers.get(name);
  const value = headers[name] ?? headers[name.toLowerCase()];
  return Array.isArray(value) ? value[0] ?? null : value ?? null;
};

const digest = async (value: string): Promise<Uint8Array> => {
  const bytes = encoder.encode(value);
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
};

export const safeEqual = async (left: string, right: string): Promise<boolean> => {
  const [a, b] = await Promise.all([digest(left), digest(right)]);
  let difference = a.length ^ b.length;
  const length = Math.max(a.length, b.length);
  for (let index = 0; index < length; index += 1) {
    difference |= (a[index] ?? 0) ^ (b[index] ?? 0);
  }
  return difference === 0;
};

const parseBasic = (header: string | null): { username: string; password: string } | null => {
  if (!header?.startsWith("Basic ")) return null;
  try {
    const decoded = atob(header.slice(6));
    const separator = decoded.indexOf(":");
    if (separator < 0) return null;
    return { username: decoded.slice(0, separator), password: decoded.slice(separator + 1) };
  } catch {
    return null;
  }
};

const parseBearer = (header: string | null): string | null => {
  if (!header?.startsWith("Bearer ")) return null;
  const token = header.slice(7).trim();
  return token || null;
};

export const hasTeamConfiguration = (): boolean => Boolean(
  process.env.TLWB_AUTH_USERNAME && process.env.TLWB_AUTH_PASSWORD,
);

export const hasWorkerConfiguration = (): boolean => Boolean(process.env.TLWB_WORKER_TOKEN);

export const hasAccountingConfiguration = (): boolean => Boolean(process.env.TLWB_DAVID_API_TOKEN);

export const isTeamAuthenticated = async (request: RequestLike): Promise<boolean> => {
  const credentials = parseBasic(requestHeader(request, "authorization"));
  if (!credentials || !hasTeamConfiguration()) return false;
  const [usernameOk, passwordOk] = await Promise.all([
    safeEqual(credentials.username, process.env.TLWB_AUTH_USERNAME ?? ""),
    safeEqual(credentials.password, process.env.TLWB_AUTH_PASSWORD ?? ""),
  ]);
  return usernameOk && passwordOk;
};

export const isWorkerAuthenticated = async (request: RequestLike): Promise<boolean> => {
  const token = parseBearer(requestHeader(request, "authorization"));
  return Boolean(token && hasWorkerConfiguration() && await safeEqual(token, process.env.TLWB_WORKER_TOKEN ?? ""));
};

export const isAccountingAuthenticated = async (request: RequestLike): Promise<boolean> => {
  if (await isTeamAuthenticated(request)) return true;
  const token = parseBearer(requestHeader(request, "authorization"));
  return Boolean(token && hasAccountingConfiguration() && await safeEqual(token, process.env.TLWB_DAVID_API_TOKEN ?? ""));
};