import { handleApiRequest } from "./api/routes";
import { PollingPipeline } from "./polling/pipeline";
import { Env } from "./types";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // 1. Check if handled by API routes (/api/*, /catalog/*, /watchlist/*, /health)
    const apiResponse = await handleApiRequest(request, env);
    if (apiResponse) return apiResponse;

    // 2. Serve static assets (React 19 / Vite SPA)
    if (env.ASSETS) {
      return await env.ASSETS.fetch(request);
    }

    return new Response("HMT Watch Monitor Worker Ready", {
      status: 200,
      headers: { "Content-Type": "text/plain" },
    });
  },

  async scheduled(controller: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    console.log(`Scheduled Cron trigger executed at ${new Date(controller.scheduledTime).toISOString()}`);
    const pipeline = new PollingPipeline(env);
    ctx.waitUntil(pipeline.run());
  },
};
