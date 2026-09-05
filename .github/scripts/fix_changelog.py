import subprocess, sys

main_content = subprocess.check_output(
    ['git', 'show', 'origin/main:CHANGELOG.md']
).decode('utf-8')

hook_section = (
    "### Release: ClawMetry will never delete another tool's Claude Code hook"
    " from your Claude Code settings (carries #5209) (2026-08-25)\n"
    "- **Who this reaches:** anyone who runs ClawMetry alongside another tool"
    " that also hooks Claude Code. GitLens now installs its own hooks with a"
    " force flag on a very large number of machines, and it is not the only"
    " one: numbat does it too, and so might something you set up by hand.\n"
    "- **These tools all write the same file, and we were not careful enough"
    " with it.** `~/.claude/settings.json` holds a list of hooks, and"
    " ClawMetry writes to it from three places. Another tool can add itself"
    " in one of two ways: as its own separate row, or by adding its command"
    " to a row that already exists. We only ever handled the first."
    " Co-installation looked fine because every tool we had seen used it.\n"
    "- **When a tool added itself to one of our rows, we deleted it.**"
    " Removing ClawMetry's hooks removed the whole row, so the other tool's"
    " hook went with it. Worse, the same thing happened without anyone"
    " uninstalling anything: the part of ClawMetry that keeps its hook up to"
    " date rewrites that file roughly every two seconds, and it deleted the"
    " neighbour within seconds of it appearing, silently. It was doing this"
    " to one of our own hooks as well.\n"
    "- **The rule now is simple: never delete a hook you did not write.**"
    " Removal works on individual hooks rather than whole rows. Ours come"
    " out, everything else stays exactly where it was, and a row is only"
    " removed once nothing is left in it.\n"
    "- **A stuck gate can no longer hold up your agent for a week.**"
    " The waiting time we installed was worked out from the longest approval"
    " window and came to seven days. If our side ever wedged, your agent"
    " waited. On GitHub Copilot, which refuses the tool call when a hook does"
    " not answer, that is your own agent brought to a halt. The wait is now"
    " capped at eight hours, adjustable with `CLAWMETRY_HOOK_TIMEOUT_MAX_S`,"
    " and set to 0 if you really do want the old behaviour. Past the cap the"
    " runtime stops the call itself rather than the approval policy deciding,"
    " which is written down rather than left to be discovered.\n"
    "- **ClawMetry not running was already fine and still is:** about two"
    " seconds, then it steps aside and your normal permission prompt appears."
    " Measured, not assumed.\n"
    "- **Verified:** 18 new tests, 6 of which were confirmed to fail against"
    " the old code, plus a harness that runs both installers against another"
    " tool in both orders and both shapes and compares the file at every step."
    " It went from 6 of 8 cases preserving the other tool's hook to 8 of 8."
    " Then run against a copy of a real machine's settings file, where"
    " numbat's 11 hooks survived a full install, refresh and uninstall cycle"
    " untouched.\n"
    "- **What this does not prove:** GitLens ships as a closed binary, so"
    " none of this shows what its force flag does to our hook. It shows that"
    " we do not damage its hook. Confirming the other direction needs a"
    " machine with GitLens actually installed.\n"
    "\n"
)

MARKER = "### Release: your agent is watched for more than loops"
idx = main_content.find(MARKER)
if idx < 0:
    print("ERROR: Marker not found in main CHANGELOG.md", file=sys.stderr)
    sys.exit(1)
merged = main_content[:idx] + hook_section + main_content[idx:]
with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
    f.write(merged)
print(f"Wrote {len(merged)} chars; hook at {idx}, watched section at {idx + len(hook_section)}")
