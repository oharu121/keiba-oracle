import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  ExperimentalEmptyAdapter,
} from "@copilotkit/runtime";

/**
 * CopilotKit API Route for Keiba Oracle.
 *
 * Connects the Next.js frontend to the Python LangGraph backend
 * via CopilotKit's AG-UI protocol.
 */
export const POST = async (req: NextRequest) => {
  const runtime = new CopilotRuntime({
    remoteEndpoints: [
      {
        url: process.env.AGENT_URL || "http://localhost:8000/copilotkit",
      },
    ],
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
