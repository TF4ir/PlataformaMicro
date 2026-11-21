#!/usr/bin/env node
/**
 * Release Artifact Verification Script (PlataformaMicro Release R1.1 - C4)
 *
 * Enforces production readiness invariants on the generated OpenNext Cloudflare bundle:
 * 1. Verifies presence and integrity of .open-next/worker.js, assets directory, and .next/BUILD_ID.
 * 2. Verifies artifact freshness (ensuring no stale build is deployed).
 * 3. Scans all bundle artifacts for forbidden sentinels (insecure write fallbacks / answer leaks).
 * 4. Validates wrangler.jsonc configuration, HTTPS protocols, and absence of service-role keys.
 * 5. Generates an immutable release-manifest.json with commit, branch, build ID, and audit details.
 */

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { resolve, join, relative } from "node:path";
import { execSync } from "node:child_process";

const REPO_ROOT = resolve(new URL(".", import.meta.url).pathname, "..");
const WEB_DIR = join(REPO_ROOT, "apps", "web");
const OPEN_NEXT_DIR = join(WEB_DIR, ".open-next");
const NEXT_DIR = join(WEB_DIR, ".next");
const WORKER_FILE = join(OPEN_NEXT_DIR, "worker.js");
const ASSETS_DIR = join(OPEN_NEXT_DIR, "assets");
const BUILD_ID_FILE = join(NEXT_DIR, "BUILD_ID");
const WRANGLER_FILE = join(WEB_DIR, "wrangler.jsonc");
const MANIFEST_FILE = join(OPEN_NEXT_DIR, "release-manifest.json");

// Forbidden sentinels: Insecure write fallbacks or sensitive solution leak functions
const FORBIDDEN_SENTINELS = [
  "startAttemptFromSupabase",
  "submitAnswerFromSupabase",
  "submitAttemptFromSupabase",
  "getAttemptResultsFromSupabase",
  "getStudentActivityFromSupabase",
];

function parseArgs() {
  const args = process.argv.slice(2);
  let buildStartTime = 0;
  let maxAgeMinutes = 60; // Default max artifact age
  let writeManifest = true;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--build-start-time" && args[i + 1]) {
      buildStartTime = Number(args[++i]);
    } else if (args[i] === "--max-age-minutes" && args[i + 1]) {
      maxAgeMinutes = Number(args[++i]);
    } else if (args[i] === "--no-manifest") {
      writeManifest = false;
    }
  }

  return { buildStartTime, maxAgeMinutes, writeManifest };
}

function stripTrailingCommas(text) {
  let insideString = false;
  let stringChar = '"';
  let isEscaped = false;
  const chars = text.split("");

  for (let i = 0; i < chars.length; i++) {
    const ch = chars[i];
    if (insideString) {
      if (isEscaped) {
        isEscaped = false;
      } else if (ch === "\\") {
        isEscaped = true;
      } else if (ch === stringChar) {
        insideString = false;
      }
      continue;
    }
    if (ch === '"' || ch === "'") {
      insideString = true;
      stringChar = ch;
      continue;
    }
    if (ch === ",") {
      let j = i + 1;
      while (j < chars.length && /\s/.test(chars[j])) {
        j++;
      }
      if (j < chars.length && (chars[j] === "}" || chars[j] === "]")) {
        chars[i] = " ";
      }
    }
  }
  return chars.join("");
}

function stripJsonComments(text) {
  let insideString = false;
  let stringChar = '"';
  let isEscaped = false;
  let out = "";

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];

    if (insideString) {
      out += ch;
      if (isEscaped) {
        isEscaped = false;
      } else if (ch === "\\") {
        isEscaped = true;
      } else if (ch === stringChar) {
        insideString = false;
      }
      continue;
    }

    if (ch === '"' || ch === "'") {
      insideString = true;
      stringChar = ch;
      out += ch;
      continue;
    }

    if (ch === "/" && next === "/") {
      // Single line comment: skip until newline
      while (i < text.length && text[i] !== "\n" && text[i] !== "\r") {
        i++;
      }
      if (i < text.length) {
        out += text[i];
      }
      continue;
    }

    if (ch === "/" && next === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) {
        i++;
      }
      i++;
      continue;
    }

    out += ch;
  }
  return stripTrailingCommas(out);
}

function getGitMetadata() {
  try {
    const commit = execSync("git rev-parse HEAD", { cwd: REPO_ROOT }).toString().trim();
    const branch = execSync("git rev-parse --abbrev-ref HEAD", { cwd: REPO_ROOT }).toString().trim();
    const commitDate = execSync("git log -1 --format=%cI", { cwd: REPO_ROOT }).toString().trim();
    const isClean = execSync("git status --porcelain", { cwd: REPO_ROOT }).toString().trim().length === 0;
    return { commit, branch, commitDate, isClean };
  } catch (err) {
    return { commit: "unknown", branch: "unknown", commitDate: "unknown", isClean: false };
  }
}

function collectJsFiles(dir) {
  const results = [];
  if (!existsSync(dir)) return results;

  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "node_modules" && entry.name !== ".cache") {
        results.push(...collectJsFiles(fullPath));
      }
    } else if (entry.isFile() && /\.(js|mjs|cjs)$/.test(entry.name)) {
      results.push(fullPath);
    }
  }
  return results;
}

export function verifyReleaseArtifact(options = {}) {
  const { buildStartTime = 0, maxAgeMinutes = 60, writeManifest = true } = options;
  console.log("===============================================================================");
  console.log("   PlataformaMicro Release Artifact Verification (R1.1 / OpenNext)");
  console.log("===============================================================================");

  const errors = [];

  // 1. Artifact Existence
  if (!existsSync(WORKER_FILE)) {
    errors.push(`Missing OpenNext Worker bundle at ${relative(REPO_ROOT, WORKER_FILE)}`);
  } else {
    const workerStats = statSync(WORKER_FILE);
    if (workerStats.size < 1000) {
      errors.push(`OpenNext Worker bundle is suspiciously small (${workerStats.size} bytes)`);
    }
  }

  if (!existsSync(ASSETS_DIR)) {
    errors.push(`Missing static assets directory at ${relative(REPO_ROOT, ASSETS_DIR)}`);
  } else {
    try {
      const assetFiles = readdirSync(ASSETS_DIR);
      if (assetFiles.length === 0) {
        errors.push(`Static assets directory at ${relative(REPO_ROOT, ASSETS_DIR)} is empty`);
      }
    } catch (err) {
      errors.push(`Failed to read static assets directory: ${err.message}`);
    }
  }

  let buildId = "";
  const altBuildIdFile = join(ASSETS_DIR, "BUILD_ID");
  const resolvedBuildIdFile = existsSync(BUILD_ID_FILE)
    ? BUILD_ID_FILE
    : existsSync(altBuildIdFile)
    ? altBuildIdFile
    : null;

  if (!resolvedBuildIdFile) {
    errors.push(`Missing Next.js BUILD_ID file at ${relative(REPO_ROOT, BUILD_ID_FILE)}`);
  } else {
    buildId = readFileSync(resolvedBuildIdFile, "utf8").trim();
    if (!buildId) {
      errors.push("Next.js BUILD_ID file is empty");
    }
  }

  if (errors.length > 0) {
    console.error("❌ Artifact Existence Checks FAILED:");
    for (const err of errors) console.error(`  - ${err}`);
    return { ok: false, errors };
  }

  // 2. Freshness Verification
  const workerStats = statSync(WORKER_FILE);
  const workerMtimeMs = workerStats.mtimeMs;
  const now = Date.now();

  if (buildStartTime > 0) {
    // Worker must have been created after build started (2000ms clock skew tolerance)
    if (workerMtimeMs < buildStartTime - 2000) {
      errors.push(
        `Stale artifact detected: ${relative(REPO_ROOT, WORKER_FILE)} mtime (${new Date(
          workerMtimeMs
        ).toISOString()}) is older than build start time (${new Date(buildStartTime).toISOString()})`
      );
    }
  } else {
    const maxAgeMs = maxAgeMinutes * 60 * 1000;
    if (now - workerMtimeMs > maxAgeMs) {
      errors.push(
        `Artifact is too old (${Math.round((now - workerMtimeMs) / 60000)} minutes old, maximum allowed: ${maxAgeMinutes} minutes)`
      );
    }
  }

  // 3. Sentinels Verification (Insecure fallbacks and solution leaks)
  console.log("🔍 Scanning bundle artifacts for insecure fallback sentinels...");
  const jsFiles = collectJsFiles(OPEN_NEXT_DIR);
  console.log(`  Scanned ${jsFiles.length} JavaScript bundle files in .open-next/`);

  const sentinelFindings = [];
  for (const filePath of jsFiles) {
    const content = readFileSync(filePath, "utf8");
    for (const sentinel of FORBIDDEN_SENTINELS) {
      if (content.includes(sentinel)) {
        sentinelFindings.push({ file: relative(REPO_ROOT, filePath), sentinel });
      }
    }
  }

  if (sentinelFindings.length > 0) {
    for (const finding of sentinelFindings) {
      errors.push(
        `FORBIDDEN SENTINEL DETECTED: '${finding.sentinel}' found in bundle file ${finding.file}`
      );
    }
  } else {
    console.log("  ✓ All forbidden sentinels absent from release bundles.");
  }

  // 4. Wrangler Configuration & URL Validation
  console.log("⚙️  Validating wrangler.jsonc configuration and environment variables...");
  if (!existsSync(WRANGLER_FILE)) {
    errors.push(`Missing wrangler configuration at ${relative(REPO_ROOT, WRANGLER_FILE)}`);
  } else {
    try {
      const rawWrangler = readFileSync(WRANGLER_FILE, "utf8");
      const wranglerConfig = JSON.parse(stripJsonComments(rawWrangler));

      if (wranglerConfig.name !== "plataformamicro") {
        errors.push(`Invalid worker name in wrangler.jsonc: expected 'plataformamicro', got '${wranglerConfig.name}'`);
      }
      if (wranglerConfig.main !== ".open-next/worker.js") {
        errors.push(`Invalid main entry in wrangler.jsonc: expected '.open-next/worker.js', got '${wranglerConfig.main}'`);
      }
      if (wranglerConfig.assets?.directory !== ".open-next/assets") {
        errors.push(`Invalid assets directory: expected '.open-next/assets', got '${wranglerConfig.assets?.directory}'`);
      }

      const vars = wranglerConfig.vars || {};
      const apiUrl = vars.NEXT_PUBLIC_API_URL || "";
      const supabaseUrl = vars.NEXT_PUBLIC_SUPABASE_URL || "";
      const supabaseAnonKey = vars.NEXT_PUBLIC_SUPABASE_ANON_KEY || vars.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "";

      if (!apiUrl) {
        errors.push("Missing NEXT_PUBLIC_API_URL in wrangler.jsonc vars");
      } else if (!apiUrl.startsWith("https://")) {
        errors.push(`NEXT_PUBLIC_API_URL must use HTTPS protocol in production release: ${apiUrl}`);
      }

      if (!supabaseUrl) {
        errors.push("Missing NEXT_PUBLIC_SUPABASE_URL in wrangler.jsonc vars");
      } else if (!supabaseUrl.startsWith("https://")) {
        errors.push(`NEXT_PUBLIC_SUPABASE_URL must use HTTPS protocol in production release: ${supabaseUrl}`);
      }

      if (!supabaseAnonKey) {
        errors.push("Missing NEXT_PUBLIC_SUPABASE_ANON_KEY or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in wrangler.jsonc vars");
      }

      // Security check: service role key must NEVER be included
      if (
        rawWrangler.includes("SUPABASE_SERVICE_ROLE_KEY") ||
        rawWrangler.includes("service_role") ||
        rawWrangler.includes("eyJh") && rawWrangler.includes("service_role")
      ) {
        errors.push("SECURITY VIOLATION: SUPABASE_SERVICE_ROLE_KEY or service-role credential detected in wrangler.jsonc");
      }

      console.log("  ✓ API URL:", apiUrl);
      console.log("  ✓ Supabase URL:", supabaseUrl);
      console.log("  ✓ Anon Key configured, service-role credential strictly absent.");
    } catch (err) {
      errors.push(`Failed to parse wrangler.jsonc: ${err.message}`);
    }
  }

  // 5. Git Metadata & Manifest
  const gitMeta = getGitMetadata();
  const verifiedAt = new Date().toISOString();

  if (errors.length > 0) {
    console.error("\n❌ RELEASE VERIFICATION FAILED with errors:");
    for (const err of errors) console.error(`  - ${err}`);
    return { ok: false, errors };
  }

  const manifest = {
    release: "R1.2-R2",
    status: "VERIFIED",
    verifiedAt,
    git: {
      commit: gitMeta.commit,
      branch: gitMeta.branch,
      commitDate: gitMeta.commitDate,
      cleanTree: gitMeta.isClean,
    },
    build: {
      buildId,
      workerMtime: new Date(workerMtimeMs).toISOString(),
      workerSizeBytes: workerStats.size,
      scannedFilesCount: jsFiles.length,
    },
    sentinelsChecked: FORBIDDEN_SENTINELS,
    security: {
      insecureWriteFallbacksEliminated: true,
      serviceRoleKeyLeaked: false,
    },
  };

  if (writeManifest) {
    writeFileSync(MANIFEST_FILE, JSON.stringify(manifest, null, 2) + "\n", "utf8");
    console.log(`📝 Generated release manifest at ${relative(REPO_ROOT, MANIFEST_FILE)}`);
  }

  console.log("\n===============================================================================");
  console.log("  ✓ RELEASE ARTIFACT VERIFICATION PASSED");
  console.log(`    Commit:   ${gitMeta.commit} (${gitMeta.branch})`);
  console.log(`    Build ID: ${buildId}`);
  console.log(`    Size:     ${(workerStats.size / 1024).toFixed(1)} KB`);
  console.log(`    Date:     ${verifiedAt}`);
  console.log("===============================================================================\n");

  return { ok: true, manifest };
}

// CLI Execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const options = parseArgs();
  const result = verifyReleaseArtifact(options);
  if (!result.ok) {
    process.exit(1);
  }
}
