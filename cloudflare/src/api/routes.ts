import { DBQueries } from "../db/queries";
import { PollingPipeline } from "../polling/pipeline";
import { Env } from "../types";

export async function handleApiRequest(request: Request, env: Env): Promise<Response | null> {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/$/, "");
  const method = request.method.toUpperCase();

  const db = new DBQueries(env.DB);
  await db.initTables();

  // Helper JSON response with CORS headers
  const jsonResponse = (data: any, status = 200) => {
    return new Response(JSON.stringify(data), {
      status,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  };

  if (method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  }

  // GET /health or /api/health
  if ((path === "/health" || path === "/api/health") && method === "GET") {
    try {
      const statusMeta = await db.getCatalogStatus();
      return jsonResponse({
        status: "healthy",
        database: "connected",
        cron_schedule: "*/2 * * * *",
        total_watches: statusMeta.total_watches,
        in_stock: statusMeta.in_stock,
        last_poll: statusMeta.last_poll,
        notification_channels: {
          ntfy: Boolean(env.NTFY_TOPIC),
          resend_email: Boolean(env.RESEND_API_KEY && env.RESEND_TO_EMAIL),
        },
        timestamp: new Date().toISOString(),
      });
    } catch (err: any) {
      return jsonResponse({ status: "error", message: err.message }, 500);
    }
  }

  // GET /api/catalog or /catalog
  if ((path === "/api/catalog" || path === "/catalog") && method === "GET") {
    const products = await db.getAllCatalogProducts();
    const formatted = products.map((p) => ({
      id: p.id,
      title: p.title || "HMT Watch",
      url: p.url,
      in_stock: Boolean(p.in_stock),
      price: p.price,
      site_name: p.site_name,
      last_seen: p.last_seen,
      created_at: p.created_at,
    }));
    return jsonResponse(formatted);
  }

  // GET /api/catalog/status or /catalog/status
  if ((path === "/api/catalog/status" || path === "/catalog/status") && method === "GET") {
    const statusMeta = await db.getCatalogStatus();
    return jsonResponse(statusMeta);
  }

  // POST /api/catalog/sync or /catalog/sync
  if ((path === "/api/catalog/sync" || path === "/catalog/sync") && method === "POST") {
    const pipeline = new PollingPipeline(env);
    const syncStats = await pipeline.phase1SyncCatalog();
    return jsonResponse({
      message: "Catalog sync complete",
      stats: syncStats,
      timestamp: new Date().toISOString(),
    });
  }

  // GET /api/watchlist or /watchlist
  if ((path === "/api/watchlist" || path === "/watchlist") && method === "GET") {
    const items = await db.getWatchlist(7);
    const formatted = items.map((p) => ({
      id: p.id,
      title: p.title || "HMT Watch",
      in_stock: Boolean(p.in_stock),
    }));
    return jsonResponse(formatted);
  }

  // POST /api/watchlist/:id or /watchlist/:id
  const matchPostWatch = path.match(/^\/(?:api\/)?watchlist\/(\d+)$/);
  if (matchPostWatch && method === "POST") {
    const catalogProductId = parseInt(matchPostWatch[1], 10);
    await db.addWatchlistItem(catalogProductId, 7);
    return jsonResponse({ message: "Added" });
  }

  // DELETE /api/watchlist/:id or /watchlist/:id
  const matchDeleteWatch = path.match(/^\/(?:api\/)?watchlist\/(\d+)$/);
  if (matchDeleteWatch && method === "DELETE") {
    const catalogProductId = parseInt(matchDeleteWatch[1], 10);
    const removed = await db.removeWatchlistItem(catalogProductId, 7);
    return jsonResponse({ message: removed ? "Removed" : "Not found" });
  }

  return null; // Not handled by API router
}
