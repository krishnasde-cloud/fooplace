import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { publicSsr } from "./src/modules/seo/devSsr.ts";

const root = path.dirname(fileURLToPath(import.meta.url));
const api = process.env.FOOPLACE_API_PROXY ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), publicSsr(root)],
  resolve: {
    alias: {
      "@": path.resolve(root, "src"),
    },
  },
  server: {
    host: process.env.FOOPLACE_VITE_HOST ?? "127.0.0.1",
    port: 5173,
    watch: {
      usePolling: process.env.CHOKIDAR_USEPOLLING === "true",
    },
    proxy: {
      "/api": {
        target: api,
        changeOrigin: true,
      },
      "/admin": {
        target: api,
        changeOrigin: true,
      },
      "/static": {
        target: api,
        changeOrigin: true,
      },
      "/sitemap.xml": {
        target: api,
        changeOrigin: true,
      },
      "/robots.txt": {
        target: api,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: (info) =>
          info.name?.endsWith(".css") ? "assets/index.css" : "assets/[name][extname]",
      },
    },
  },
});
