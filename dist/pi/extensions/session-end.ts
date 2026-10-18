/**
 * Session-end cleanup for the deep-plan pi build.
 *
 * Original to this project (not vendored); listed in ../THIRD_PARTY_LICENSES.md.
 * pi's counterpart of the Claude Code SessionEnd hook: on session_shutdown it runs
 * the build's cleanup.py with no session id. What that run removes, and why a
 * repeat is harmless, is owned by skills/deep-plan/hooks/cleanup.py.
 */

import { spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// cleanup.py sits one level above this file's folder; the pi profile's extra_files
// owns that layout, so a missing script is reported rather than silently skipped.
const BUILD_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CLEANUP_SCRIPT = path.join(BUILD_ROOT, "skills", "deep-plan", "hooks", "cleanup.py");
// Cap the run so shutdown never hangs.
const CLEANUP_TIMEOUT_MS = 10_000;

export default function sessionEnd(pi: ExtensionAPI) {
	pi.on("session_shutdown", async () => {
		if (!fs.existsSync(CLEANUP_SCRIPT)) {
			console.warn(`deep-plan: cleanup script not found at ${CLEANUP_SCRIPT}; build layout changed?`);
			return;
		}
		try {
			// Synchronous so cleanup finishes before pi exits; failures are swallowed
			// because cleanup must never block or break shutdown.
			spawnSync("python3", [CLEANUP_SCRIPT], { input: "", stdio: ["pipe", "ignore", "ignore"], timeout: CLEANUP_TIMEOUT_MS });
		} catch {
			// python3 missing or the spawn failed: nothing to clean up from here.
		}
	});
}
