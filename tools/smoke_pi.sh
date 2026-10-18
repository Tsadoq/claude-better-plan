#!/usr/bin/env bash
# Manual end-to-end smoke test of the pi build (dist/pi) in a real pi.
#
# The vendored pi extensions have no test runner in this repo; pytest pins only
# their source text. This script checks what only a running pi can show, and
# prints PASS or FAIL per check, exiting non-zero on any FAIL:
#   1. the package registers exactly the planned tools (hosts/pi/tools.py);
#   2. questionnaire answers "cannot ask in this mode" when pi has no UI;
#   3. subagent discovers all six dp-* agents shipped in the build;
#   4. a dp-research-shallow child process can call web_search;
#   5. session end removes a stale /tmp/deep-plan-* sandbox.
#
# Run it after any change under hosts/pi/ (and a re-render). It needs pi and npm
# on PATH and a configured model provider: the provider and model come from your
# real pi settings, and auth.json is symlinked (not copied) so a token refresh
# during the run lands in your real credentials. Everything else lives in a
# throwaway PI_CODING_AGENT_DIR that is deleted on exit. SMOKE_MODEL (a pi --model
# pattern such as <provider>/<model>) overrides the model; SMOKE_TIMEOUT (seconds,
# default 180) bounds each pi run, so a provider that never answers fails instead
# of hanging; KEEP=1 keeps the run's files after a failure.

set -u

# First, before any external command: a missing pi must never read as a pass.
if ! command -v pi >/dev/null 2>&1; then
	echo "smoke_pi: pi not found on PATH; install pi (https://pi.dev) and retry" >&2
	exit 2
fi
if ! command -v npm >/dev/null 2>&1; then
	echo "smoke_pi: npm not found on PATH; it installs the package's npm extensions" >&2
	exit 2
fi

SMOKE_TIMEOUT=${SMOKE_TIMEOUT:-180}
case $SMOKE_TIMEOUT in
'' | *[!0-9]* | 0)
	echo "smoke_pi: SMOKE_TIMEOUT must be a positive whole number of seconds, got '$SMOKE_TIMEOUT'" >&2
	exit 2
	;;
esac
# The exit status run_pi reports when SMOKE_TIMEOUT ran out (GNU timeout's code).
TIMED_OUT=124

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REAL_AGENT_DIR=${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}
# cleanup.py's sandbox prefix is deep-plan-, and its retention is 7 days.
STALE_SANDBOX=/tmp/deep-plan-smoke
STALE_MTIME=200001010000

WORK=$(mktemp -d "${TMPDIR:-/tmp}/smoke-pi.XXXXXX")
trap 'rm -rf "$WORK" "$STALE_SANDBOX"' EXIT
# A signal still runs the EXIT cleanup above.
trap 'exit 130' INT
trap 'exit 143' TERM
PKG=$WORK/pkg
AGENT_DIR=$WORK/agent
RUN_DIR=$WORK/cwd
PROBE=$WORK/probe.ts
TOOLS_FILE=$WORK/tools.jsonl
mkdir -p "$PKG/dist" "$AGENT_DIR" "$RUN_DIR"

FAILED=0

pass() { echo "PASS $1"; }
fail() {
	echo "FAIL $1: $2"
	FAILED=1
}

# pi loads a local package in place and never installs its dependencies, so the
# build is copied out and its npm extensions installed there, leaving the
# checkout untouched.
install_package() {
	cp "$REPO/package.json" "$PKG/"
	cp -R "$REPO/dist/pi" "$PKG/dist/pi"
	(cd "$PKG" && npm install --omit=peer --no-audit --no-fund --silent) || return 1
}

# A settings.json holding only this package plus the real provider and model, so
# no other installed package's tools leak into check 1.
write_agent_dir() {
	if [ -e "$REAL_AGENT_DIR/auth.json" ]; then
		ln -s "$REAL_AGENT_DIR/auth.json" "$AGENT_DIR/auth.json"
	fi
	if [ -e "$REAL_AGENT_DIR/models-store.json" ]; then
		cp "$REAL_AGENT_DIR/models-store.json" "$AGENT_DIR/"
	fi
	python3 - "$REAL_AGENT_DIR/settings.json" "$AGENT_DIR/settings.json" "$PKG" <<'PY'
import json, sys
from pathlib import Path

real, out, pkg = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
source = json.loads(real.read_text()) if real.exists() else {}
kept = {k: source[k] for k in ("defaultProvider", "defaultModel", "defaultThinkingLevel") if k in source}
out.write_text(json.dumps({**kept, "quietStartup": True, "packages": [pkg]}, indent=2))
PY
}

# Records every tool pi knows at session start, with the file that registered it,
# because pi's JSON output never lists tools.
write_probe() {
	cat >"$PROBE" <<'TS'
import * as fs from "node:fs";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function probe(pi: ExtensionAPI) {
	pi.on("session_start", async () => {
		const lines = pi.getAllTools().map((t) => JSON.stringify({ name: t.name, path: t.sourceInfo.path }));
		fs.writeFileSync(process.env.SMOKE_TOOLS_FILE ?? "", `${lines.join("\n")}\n`);
	});
}
TS
}

# Runs argv[2:] for at most argv[1] seconds, exiting 124 on timeout. macOS ships
# no GNU timeout. The command gets its own process group so a kill also reaches
# the subagent children pi spawns.
WATCHDOG='
import os, signal, subprocess, sys

signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
child = subprocess.Popen(sys.argv[2:], start_new_session=True)
code = 124
try:
    code = child.wait(timeout=int(sys.argv[1]))
except subprocess.TimeoutExpired:
    pass
finally:
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
sys.exit(code)
'

# run_pi OUT PROMPT: one print-mode run in the throwaway agent dir, JSON events to
# OUT. Returns TIMED_OUT when pi is still running after SMOKE_TIMEOUT seconds.
run_pi() {
	local model_args=()
	[ -n "${SMOKE_MODEL:-}" ] && model_args=(--model "$SMOKE_MODEL")
	(cd "$RUN_DIR" && PI_CODING_AGENT_DIR=$AGENT_DIR XDG_STATE_HOME=$WORK/state SMOKE_TOOLS_FILE=$TOOLS_FILE \
		python3 -c "$WATCHDOG" "$SMOKE_TIMEOUT" \
		pi -p --mode json --no-session -e "$PROBE" ${model_args[@]+"${model_args[@]}"} "$2") >"$1" 2>"$1.stderr"
}

# run_check NAME OUT PROMPT: run_pi for one check; a timed-out run FAILs NAME and
# returns non-zero so the check skips its assertions.
run_check() {
	run_pi "$2" "$3"
	[ $? -ne "$TIMED_OUT" ] && return 0
	fail "$1" "pi did not finish within ${SMOKE_TIMEOUT}s (see $2)"
	return 1
}

# model_error EVENTS: the provider error of the last assistant reply, or nothing.
# Checks 2 to 4 need a working model, so a broken provider stops the run here.
model_error() {
	python3 - "$1" <<'PY'
import json, sys

error, reply = "no assistant reply", {}
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        event = json.loads(line)
    except ValueError:
        continue
    message = event.get("message") or {}
    if event.get("type") == "message_end" and message.get("role") == "assistant":
        reply = message
        error = message.get("errorMessage", "") if message.get("stopReason") == "error" else ""
print(f"{reply.get('provider')}/{reply.get('model')}: {error[:300]}" if error else "")
PY
}

# tool_result EVENTS TOOL: the JSON of every finished TOOL call in EVENTS, one per line.
tool_result() {
	python3 - "$1" "$2" <<'PY'
import json, sys

for line in open(sys.argv[1], encoding="utf-8"):
    try:
        event = json.loads(line)
    except ValueError:
        continue
    if event.get("type") == "tool_execution_end" and event.get("toolName") == sys.argv[2]:
        print(json.dumps(event.get("result")))
PY
}

check_tools() {
	local verdict
	verdict=$(python3 - "$REPO" "$TOOLS_FILE" "$PKG" 2>&1 <<'PY'
import json, sys
from pathlib import Path

repo, tools_file, pkg = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, repo)
from hosts.pi.tools import NPM_TOOLS, VENDORED_TOOLS

if not tools_file.exists():
    sys.exit("the probe extension never ran, so no tool list was recorded")
tools = [json.loads(line) for line in tools_file.read_text().splitlines() if line]
ours = {t["name"] for t in tools if Path(t["path"]).resolve().is_relative_to(Path(pkg).resolve())}
planned = set(VENDORED_TOOLS) | set(NPM_TOOLS)
if ours != planned:
    sys.exit(f"package registered {sorted(ours)}; planned {sorted(planned)}")
PY
) || { fail "1 tool list" "$verdict"; return; }
	pass "1 tool list"
}

check_questionnaire() {
	local out=$WORK/questionnaire.jsonl
	run_check "2 questionnaire fallback" "$out" \
		"Call the questionnaire tool exactly once with one question, \"Pick a colour\", options red and blue. Then stop." || return
	if tool_result "$out" questionnaire | grep -q "cannot ask in this mode"; then
		pass "2 questionnaire fallback"
	else
		fail "2 questionnaire fallback" "no questionnaire result said \"cannot ask in this mode\" (see $out)"
	fi
}

check_agent_discovery() {
	local out=$WORK/discovery.jsonl result agent missing=""
	run_check "3 agent discovery" "$out" \
		"Call the subagent tool exactly once with agent \"no-such-agent\" and task \"noop\". Then stop." || return
	result=$(tool_result "$out" subagent)
	for agent in "$REPO"/dist/pi/agents/dp-*.md; do
		agent=$(basename "$agent" .md)
		case $result in *"$agent"*) ;; *) missing="$missing $agent" ;; esac
	done
	if [ -z "$result" ]; then
		fail "3 agent discovery" "the model never called subagent (see $out)"
	elif [ -n "$missing" ]; then
		fail "3 agent discovery" "unknown-agent reply lacks:$missing"
	else
		pass "3 agent discovery"
	fi
}

check_child_web_search() {
	local out=$WORK/child.jsonl
	run_check "4 child web access" "$out" \
		"Call the subagent tool exactly once with agent \"dp-research-shallow\" and task \"Use web_search once to find the latest stable Python release, then answer in one line.\" Then stop." || return
	# The child's own tool calls ride in the subagent result's details.
	if tool_result "$out" subagent | python3 -c '
import json, sys

def calls(node):
    if isinstance(node, dict):
        if node.get("type") == "toolCall":
            yield node.get("name")
        for value in node.values():
            yield from calls(value)
    elif isinstance(node, list):
        for value in node:
            yield from calls(value)

sys.exit(0 if any("web_search" in calls(json.loads(l)) for l in sys.stdin if l.strip()) else 1)
'; then
		pass "4 child web access"
	else
		fail "4 child web access" "dp-research-shallow made no web_search call (see $out)"
	fi
}

main() {
	install_package || { echo "smoke_pi: npm install of the pi package failed" >&2; exit 1; }
	write_agent_dir
	write_probe

	# Check 5's sandbox must exist before the first run, whose exit cleans it.
	mkdir -p "$STALE_SANDBOX"
	touch -t "$STALE_MTIME" "$STALE_SANDBOX"
	local status=0
	run_pi "$WORK/startup.jsonl" "Reply with the single word ok." || status=$?
	if [ "$status" -eq "$TIMED_OUT" ]; then
		echo "smoke_pi: the model did not answer within ${SMOKE_TIMEOUT}s; fix the provider, set SMOKE_MODEL, or raise SMOKE_TIMEOUT" >&2
		exit 1
	fi
	local broken
	broken=$(model_error "$WORK/startup.jsonl")
	if [ -n "$broken" ]; then
		echo "smoke_pi: the model is not usable ($broken); fix the provider or set SMOKE_MODEL" >&2
		exit 1
	fi
	check_tools
	if [ -e "$STALE_SANDBOX" ]; then
		fail "5 session end" "$STALE_SANDBOX survived a pi run"
	else
		pass "5 session end"
	fi

	check_questionnaire
	check_agent_discovery
	check_child_web_search

	if [ "$FAILED" -ne 0 ]; then
		echo "smoke_pi: FAILED (artifacts deleted on exit; set KEEP=1 to keep $WORK)" >&2
		[ "${KEEP:-0}" = 1 ] && trap - EXIT
		exit 1
	fi
	echo "smoke_pi: all checks passed"
}

main
