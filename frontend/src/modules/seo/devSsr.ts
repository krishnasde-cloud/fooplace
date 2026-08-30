import type { IncomingMessage, ServerResponse } from "node:http";
import fs from "node:fs";
import path from "node:path";
import type { Plugin, ViteDevServer } from "vite";
import { isPublicSeoPath, listingIdFromPath, sellerIdFromPath } from "./publicPath.ts";

function ssrDataScript(data: unknown): string {
  return `<script type="application/json" id="fooplace-ssr-data">${JSON.stringify(data).replaceAll("<", "\\u003c")}</script>`;
}

function apiOrigin(): string {
  return process.env.FOOPLACE_API_PROXY ?? "http://127.0.0.1:8000";
}

function pagePath(url = "/"): string {
  return (url.split("?")[0] || "/") as string;
}

function isHtmlRequest(req: IncomingMessage): boolean {
  const accept = req.headers.accept ?? "";
  if (req.method !== "GET" && req.method !== "HEAD") {
    return false;
  }
  if (accept.includes("text/html")) {
    return true;
  }
  return !accept.includes("application/json") && !pagePath(req.url).includes(".");
}

async function loadPublicData(pathname: string) {
  const origin = apiOrigin();
  const listingId = listingIdFromPath(pathname);
  if (listingId !== null) {
    const response = await fetch(`${origin}/api/listings/${listingId}/`);
    if (!response.ok) {
      return { listing: null };
    }
    return { listing: await response.json() };
  }
  const sellerId = sellerIdFromPath(pathname);
  if (sellerId !== null) {
    const response = await fetch(`${origin}/api/reviews/sellers/${sellerId}/`);
    if (!response.ok) {
      return { seller: null };
    }
    return { seller: await response.json() };
  }
  const response = await fetch(`${origin}/api/listings/`);
  if (!response.ok) {
    return { listings: [] };
  }
  const body = (await response.json()) as { listings?: unknown[] };
  return { listings: body.listings ?? [] };
}

async function writePublicHtml(
  server: ViteDevServer,
  req: IncomingMessage,
  res: ServerResponse,
  rootDir: string,
): Promise<void> {
  const pathname = pagePath(req.url);
  const { renderPublicPage } = await server.ssrLoadModule("/src/modules/seo/render.tsx");
  const data = await loadPublicData(pathname);
  const rendered = renderPublicPage(pathname, "http://localhost:5173", data);
  let html = fs.readFileSync(path.join(rootDir, "index.html"), "utf8");
  html = await server.transformIndexHtml(pathname, html);
  html = html.replace('<meta name="robots" content="noindex, nofollow" />', "");
  html = html.replace("<title>Fooplace</title>", "");
  html = html.replace("<!--app-head-->", rendered.head);
  html = html.replace("<!--app-html-->", `${rendered.body}${ssrDataScript(data)}`);
  res.statusCode = rendered.status;
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  res.setHeader("X-Robots-Tag", rendered.robots);
  res.end(html);
}

export function publicSsr(rootDir: string): Plugin {
  return {
    name: "fooplace-public-ssr",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const pathname = pagePath(req.url);
        if (!isHtmlRequest(req) || !isPublicSeoPath(pathname)) {
          next();
          return;
        }
        try {
          await writePublicHtml(server, req, res, rootDir);
        } catch {
          next();
        }
      });
    },
  };
}
