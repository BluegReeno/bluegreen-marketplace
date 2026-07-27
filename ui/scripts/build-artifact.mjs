/**
 * Shared post-build step for every ui/<name>/ artifact app.
 * Invoked as `node ../scripts/build-artifact.mjs <artifact-name>` from within
 * ui/<name>/ immediately after `vite build`. Responsibilities, in order:
 *   1. Read dist/index.html produced by the just-completed vite build.
 *   2. Size guard: hard-fail past 16 MiB (the Cowork/Claude Code rendered
 *      ceiling), warn past 2 MiB.
 *   3. Prepend a provenance stamp comment (build date, source commit,
 *      annotation-core version) right after <!doctype html>.
 *   4. Branch on ARTIFACT_TARGET (default "cowork"): keep the full document,
 *      or strip the <html>/<head>/<body> wrapper for a "fragment" target.
 *   5. Write the result to <repo-root>/plugins/hal/artifacts/<name>.html.
 * Exit 0 = artifact written. Exit 1 = missing input, size ceiling, or bad args.
 */

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as cheerio from "cheerio";

const SIZE_CEILING = 16 * 1024 * 1024; // 16 MiB — hard Cowork/Claude Code ceiling
const SIZE_WARN = 2 * 1024 * 1024; // 2 MiB — well below the ceiling

const name = process.argv[2];
if (!name) {
  console.error("ERROR: usage: node build-artifact.mjs <artifact-name>");
  process.exit(1);
}

// Resolve repo root from this script's own location: ui/scripts/ -> ../.. == repo root.
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..", "..");
const appDir = path.join(repoRoot, "ui", name);
const distFile = path.join(appDir, "dist", "index.html");

if (!fs.existsSync(distFile)) {
  console.error(`ERROR: no build output at ${distFile} — run \`vite build\` first`);
  process.exit(1);
}

let html = fs.readFileSync(distFile, "utf8");

// 2. Size guard (checked on the raw vite output before the stamp is added).
const bytes = Buffer.byteLength(html, "utf8");
if (bytes > SIZE_CEILING) {
  console.error(
    `ERROR: [${name}] ${bytes} bytes exceeds the 16 MiB artifact ceiling`,
  );
  process.exit(1);
}
if (bytes > SIZE_WARN) {
  console.warn(
    `WARN: [${name}] ${bytes} bytes exceeds the 2 MiB warn threshold (ceiling is 16 MiB)`,
  );
}

// 3. Provenance stamp.
const commit = execSync("git rev-parse --short HEAD", {
  cwd: repoRoot,
})
  .toString()
  .trim();
const buildDate = new Date().toISOString();

let annotationCore = "n/a";
try {
  const pkg = JSON.parse(
    fs.readFileSync(path.join(appDir, "package.json"), "utf8"),
  );
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  if (deps["@bluegreeno/annotation-core"]) {
    annotationCore = deps["@bluegreeno/annotation-core"];
  }
} catch {
  // no package.json / no dependency — leave "n/a"
}

const stamp = `<!-- build: date=${buildDate} commit=${commit} annotation-core=${annotationCore} -->`;
html = html.replace(/(<!doctype html>)/i, `$1\n${stamp}`);

// 4. Target-flag branch.
const target = process.env.ARTIFACT_TARGET || "cowork";
let output;
if (target === "fragment") {
  // vite-plugin-singlefile inlines <script>/<style> into <head>, so a
  // body-only extraction would silently drop the entire bundle. Concatenate
  // head + body to keep both while dropping the wrapper tags.
  const $ = cheerio.load(html);
  output = ($("head").html() || "") + ($("body").html() || "");
} else if (target === "cowork") {
  output = html;
} else {
  console.error(
    `ERROR: unknown ARTIFACT_TARGET="${target}" (expected "cowork" or "fragment")`,
  );
  process.exit(1);
}

// 5. Write the committed artifact.
const outDir = path.join(repoRoot, "plugins", "hal", "artifacts");
fs.mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, `${name}.html`);
fs.writeFileSync(outFile, output);
console.log(
  `OK: [${name}] wrote ${path.relative(repoRoot, outFile)} (${Buffer.byteLength(output, "utf8")} bytes, target=${target})`,
);
