import accounting from "../../_data/accounting.generated.js";
import { json, methodNotAllowed, unauthorized } from "../../_lib/http.js";
import { isAccountingAuthenticated } from "../../_lib/security.js";

export type AccountingResource = "summary" | "collections" | "events" | "inside_sales";

export const accountingHandler = async (request: Request, resource: AccountingResource): Promise<Response> => {
  if (request.method !== "GET") return methodNotAllowed(["GET"]);
  if (!await isAccountingAuthenticated(request)) return unauthorized("Bearer");
  return json({
    schema_version: accounting.schema_version,
    generated_at: accounting.generated_at,
    source_as_of: accounting.source_as_of,
    freshness: accounting.freshness,
    resource,
    data: accounting[resource],
  });
};