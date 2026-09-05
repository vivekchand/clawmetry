## Unreleased

### Release: the kill switch actually reaches the process (#5529, shipped in 0.12.815) (2026-09-05)
- **Why:** on 0.12.812, Pause / Stop / Kill returned `Pause did not succeed: session_not_in_claude_map` for every Claude Code session on a founder node — and the same resolver miss meant the daemon's autonomous Guard policies could not actuate on any family runtime either. The product's one intervention surface was inert for 26 of the 27 runtimes it offers it on. Nodes auto-update, so publishing is what makes the fix real.
- **What:** this release carries #5529. Daemon-side change (`clawmetry/process_control.py`), so the cloud pin follows.
- **Verified:** #5529 shipped 5 tests proven red against the unfixed file, plus a real-process pause/resume/kill through `sync._guard_actuate` using the exact id the Guard tab posts, plus all six live Guard rows on the founder node resolving to running pids. The three control test files also join the moat-tests job, where they had never run before.

