import { accountingHandler } from "./_handler.js";
export const GET = (request: Request) => accountingHandler(request, "inside_sales");
