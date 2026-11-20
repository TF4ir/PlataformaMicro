#!/usr/bin/env node
/**
 * Hardened Cloudflare Workers Release & Deployment Pipeline (PlataformaMicro Release R1.1 - C3)
 *
 * Orchestrates safe, reproducible release deployments to Cloudflare:
 * 1. Working tree cleanliness verification (ensuring commit reproducibility).
 * 2. Purges any stale build artifacts (.open-next / .next).
 * 3. Builds Cloudflare artifact using OpenNext.
 * 4. Verifies newly generated artifact freshness, absence of insecure sentinels, and valid HTTPS URLs.
 * 5. Generates immutable release manifest (commit, branch, build ID, timestamp).
 * 6. Publishes to Cloudflare using validated Wrangler CLI options (--message, --tag, --dry-run).
 *
 * Safeguard: By default, runs in --dry-run mode unless --publish is explicitly specified.
 */

import { execSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { resolve, join } from "node:path";
import { verifyReleaseArtifact } from "./verify-release-artifact.mjs";

const REPO_ROOT = resolve(new URL(".", import.meta.url).pathname, "..");
const WEB_DIR = join(REPO_ROOT, "apps", "web");
const OPEN_NEXT_DIR = join(WEB_DIR, ".open-next");
const NEXT_DIR = join(WEB_DIR, ".next");

function parseCliArgs() {
  const args = process.argv.slice(2);
  let dryRun = false;
  let publish = false;
  let allowDirty = false;
  let skipBuild = false;

  for (const arg of args) {
    if (arg === "--dry-run") dryRun = true;
    else if (arg === "--publish") publish = true;
    else if (arg === "--allow-dirty") allowDirty = true;
    else if (arg === "--skip-build") skipBuild = true;
  }

  // If --publish is not passed, force --dry-run for safety
  if (!publish) {
    dryRun = true;
  }

  return { dryRun, publish, allowDirty, skipBuild };
}

function runCommand(command, cwd = REPO_ROOT) {
  console.log(`\n▶ [EXEC] ${command} (in ${cwd === REPO_ROOT ? "." : "apps/web"})`);
  try {
    execSync(command, { cwd, stdio: "inherit" });
    return true;
  } catch (err) {
    console.error(`❌ Command failed: ${command}`);
    return false;
  }
}

async function main() {
  const { dryRun, publish, allowDirty, skipBuild } = parseCliArgs();

  console.log("===============================================================================");
  console.log("   PlataformaMicro Cloudflare Release Pipeline (R1.1 - Coordinated Deploy)");
  console.log(`   Mode: ${publish && !dryRun ? "🚨 PRODUCTION PUBLISH" : "🛡️  DRY-RUN (Safe Verification)"}`);
  console.log("===============================================================================");

  // 1. Working Tree Cleanliness Check
  console.log("\n[Step 1/6] Checking git working tree cleanliness...");
  let porcelainStatus = "";
  try {
    porcelainStatus = execSync("git status --porcelain", { cwd: REPO_ROOT }).toString().trim();
  } catch (err) {
    console.error("❌ Failed to query git status:", err.message);
    process.exit(1);
  }

  if (porcelainStatus.length > 0) {
    if (!allowDirty) {
      console.error("❌ RELEASE ABORTED: Git working tree is dirty.");
      console.error("   Uncommitted or untracked changes detected:");
      console.error(porcelainStatus);
      console.error("\n   All release deployments must correspond to an immutable, committed git tree.");
      console.error("   Pass --allow-dirty ONLY for local debugging.");
      process.exit(1);
    } else {
      console.warn("⚠️  WARNING: Running with dirty tree (--allow-dirty flag enabled).");
    }
  } else {
    console.log("  ✓ Working tree is clean.");
  }

  const commitHash = execSync("git rev-parse HEAD", { cwd: REPO_ROOT }).toString().trim();
  const branchName = execSync("git rev-parse --abbrev-ref HEAD", { cwd: REPO_ROOT }).toString().trim();
  console.log(`  Target Commit: ${commitHash} (${branchName})`);

  let buildStartTime = Date.now();

  if (!skipBuild) {
    // 2. Clean previous build artifacts
    console.log("\n[Step 2/6] Purging previous build artifacts to prevent stale deployments...");
    if (existsSync(OPEN_NEXT_DIR)) {
      rmSync(OPEN_NEXT_DIR, { recursive: true, force: true });
      console.log("  ✓ Purged apps/web/.open-next");
    }
    if (existsSync(NEXT_DIR)) {
      rmSync(NEXT_DIR, { recursive: true, force: true });
      console.log("  ✓ Purged apps/web/.next");
    }

    // 3. Build Cloudflare with OpenNext
    buildStartTime = Date.now();
    console.log("\n[Step 3/6] Building Cloudflare Worker bundle with OpenNext...");
    const buildSuccess = runCommand(
      "npm run build:cloudflare",
      WEB_DIR
    );

    if (!buildSuccess) {
      console.error("❌ Cloudflare build with OpenNext FAILED.");
      process.exit(1);
    }
  } else {
    console.log("\n[Step 2-3/6] Skipping build (--skip-build specified).");
  }

  // 4. Verify freshly generated release artifact
  console.log("\n[Step 4/6] Verifying freshly generated release artifact...");
  const verification = verifyReleaseArtifact({
    buildStartTime: skipBuild ? 0 : buildStartTime,
    maxAgeMinutes: 60,
    writeManifest: true,
  });

  if (!verification.ok) {
    console.error("❌ Release verification FAILED. Aborting publication.");
    process.exit(1);
  }

  const { buildId } = verification.manifest.build;

  // 5. Audit Log & Record
  console.log("[Step 5/6] Audit Record Summary:");
  console.log(`  - Commit:    ${commitHash}`);
  console.log(`  - Branch:    ${branchName}`);
  console.log(`  - Build ID:  ${buildId}`);
  console.log(`  - Timestamp: ${verification.manifest.verifiedAt}`);

  // 6. Publication via Wrangler
  console.log("\n[Step 6/6] Publishing Worker to Cloudflare...");
  const releaseMessage = `Release R1.1 commit ${commitHash.slice(0, 7)} (${branchName})`;
  const releaseTag = `r1-${buildId.slice(0, 12)}`;

  // Validated options for Wrangler 4.158.0:
  // --message: A descriptive message for this Worker Version
  // --tag: A tag for this Worker Version
  // --dry-run: Compile a project and run checks without actually uploading
  const wranglerArgs = [
    "npx --no-install wrangler deploy",
    `--message "${releaseMessage}"`,
    `--tag "${releaseTag}"`,
  ];

  if (dryRun) {
    wranglerArgs.push("--dry-run");
  }

  const wranglerCmd = wranglerArgs.join(" ");

  if (dryRun) {
    console.log("🛡️  Executing publication in DRY-RUN mode...");
    const deploySuccess = runCommand(wranglerCmd, WEB_DIR);
    if (!deploySuccess) {
      console.error("❌ Wrangler dry-run check failed.");
      process.exit(1);
    }
    console.log("\n===============================================================================");
    console.log("  ✓ RELEASE READY (DRY-RUN VERIFIED)");
    console.log(`    Wrangler dry-run succeeded for commit ${commitHash}.`);
    console.log("    To publish to Cloudflare production when ready, run with: --publish");
    console.log("===============================================================================\n");
  } else {
    console.log("🚨 EXECUTING ACTUAL CLOUDFLARE PRODUCTION DEPLOYMENT...");
    const deploySuccess = runCommand(wranglerCmd, WEB_DIR);
    if (!deploySuccess) {
      console.error("❌ Wrangler production deployment FAILED.");
      process.exit(1);
    }
    console.log("\n===============================================================================");
    console.log("  🚀 RELEASE SUCCESSFULLY PUBLISHED TO CLOUDFLARE");
    console.log(`    Commit:   ${commitHash}`);
    console.log(`    Build ID: ${buildId}`);
    console.log("===============================================================================\n");
  }
}

main().catch((err) => {
  console.error("Fatal release error:", err);
  process.exit(1);
});
