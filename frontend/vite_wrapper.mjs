import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import { build, createServer } from "vite";

const command = process.argv[2] ?? "build";
const cwd = process.cwd();

if (command === "build") {
  // Copy sources into a real directory so Vite 8 / Rolldown do not see
  // mixed sandbox vs execroot paths when emitting index.html.
  const work = path.join(cwd, ".vite-work");
  if (existsSync(work)) {
    rmSync(work, { recursive: true, force: true });
  }
  mkdirSync(work);

  for (const name of [
    "index.html",
    "vite.config.ts",
    "package.json",
    "src",
    "public",
    "tsconfig.json",
    "tsconfig.app.json",
    "tsconfig.node.json",
    ".env",
    ".env.local",
    ".env.production",
    ".env.production.local",
  ]) {
    const from = path.join(cwd, name);
    if (existsSync(from)) {
      cpSync(from, path.join(work, name), { recursive: true });
    }
  }

  await build({
    root: work,
    configFile: path.join(work, "vite.config.ts"),
  });

  cpSync(path.join(work, "dist"), path.join(cwd, "dist"), { recursive: true });
  rmSync(work, { recursive: true, force: true });
} else if (command === "dev" || command === "serve") {
  const server = await createServer();
  await server.listen();
  server.printUrls();
} else {
  throw new Error(`Unknown vite command: ${command}`);
}
