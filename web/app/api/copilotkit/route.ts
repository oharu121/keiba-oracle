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
  const agentUrl = process.env.AGENT_URL;

  if (!agentUrl) {
    console.error("AGENT_URL environment variable is not configured");
    return new Response(
      JSON.stringify({
        error: "configuration_error",
        message: "AGENT_URL environment variable is not configured. Please set it in Vercel dashboard.",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  const runtime = new CopilotRuntime({
    remoteEndpoints: [
      {
        url: agentUrl,
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

/**
 * GET endpoint for debugging - confirms AGENT_URL is configured.
 * Access via: GET /api/copilotkit
 */
export const GET = async () => {
  const agentUrl = process.env.AGENT_URL;
  return new Response(
    JSON.stringify({
      configured: !!agentUrl,
      agentUrl: agentUrl ? `${agentUrl.substring(0, 30)}...` : null,
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
};
