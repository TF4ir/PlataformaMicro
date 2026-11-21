#!/usr/bin/env node
/**
 * Cloudflare Workers Builds - Wrangler CI Match Tag Patch
 *
 * Resolves Cloudflare Workers Builds Issue #15682:
 * "non-production branch builds pass a WRANGLER_CI_MATCH_TAG that belongs to no Worker,
 * so every preview deploy fails with:
 * 'The name in your wrangler.jsonc file (plataformamicro) must match the name of your Worker.'"
 *
 * When WRANGLER_CI_MATCH_TAG is deleted, Wrangler's internal verifyWorkerMatchesCITag()
 * safely skips the tag comparison check and deploys the worker cleanly.
 */

import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

const PATCH_SENTINEL = "// WRANGLER_CI_MATCH_TAG_PATCHED";
const PATCH_CODE = `${PATCH_SENTINEL}
// Workaround for Cloudflare Workers Builds issue #15682
if (process.env.WRANGLER_CI_MATCH_TAG) {
  delete process.env.WRANGLER_CI_MATCH_TAG;
}
`;

function findTargets() {
  const targets = new Set();

  // 1. Try standard Node.js module resolution
  try {
    const pkgPath = require.resolve("wrangler/package.json");
    const dir = path.dirname(pkgPath);
    targets.add(path.join(dir, "bin/wrangler.js"));
    targets.add(path.join(dir, "wrangler-dist/cli.js"));
  } catch (_) {
    // fallback if not resolvable via standard require
  }

  // 2. Traversal fallbacks across common monorepo boundaries
  const searchRoots = [
    process.cwd(),
    __dirname,
    path.resolve(__dirname, ".."),
    path.resolve(__dirname, "../.."),
    path.resolve(__dirname, "../../.."),
    path.resolve(process.cwd(), ".."),
    path.resolve(process.cwd(), "../.."),
  ];

  for (const root of searchRoots) {
    const candidates = [
      path.join(root, "node_modules/wrangler/bin/wrangler.js"),
      path.join(root, "node_modules/wrangler/wrangler-dist/cli.js"),
      path.join(root, "apps/web/node_modules/wrangler/bin/wrangler.js"),
      path.join(root, "apps/web/node_modules/wrangler/wrangler-dist/cli.js"),
    ];

    for (const c of candidates) {
      if (fs.existsSync(c)) {
        targets.add(path.resolve(c));
      }
    }
  }

  return Array.from(targets).filter((p) => fs.existsSync(p));
}

function applyPatch(filePath) {
  try {
    let content = fs.readFileSync(filePath, "utf8");
    if (content.includes(PATCH_SENTINEL)) {
      return { filePath, status: "ALREADY_PATCHED" };
    }

    if (content.startsWith("#!")) {
      const firstNewline = content.indexOf("\n");
      if (firstNewline !== -1) {
        content =
          content.slice(0, firstNewline + 1) +
          PATCH_CODE +
          content.slice(firstNewline + 1);
      } else {
        content = content + "\n" + PATCH_CODE;
      }
    } else {
      content = PATCH_CODE + content;
    }

    fs.writeFileSync(filePath, content, "utf8");
    return { filePath, status: "PATCHED" };
  } catch (err) {
    return { filePath, status: "ERROR", error: err.message };
  }
}

function main() {
  const targets = findTargets();
  if (targets.length === 0) {
    console.log("[patch-wrangler-ci] No Wrangler installations found to patch.");
    return;
  }

  for (const target of targets) {
    const res = applyPatch(target);
    console.log(`[patch-wrangler-ci] ${res.status}: ${res.filePath}`);
  }
}

main();
