# Install-script finding, event queue and hook-failure fixes

These notes describe #6335, #6313 and #6321, which shipped in 0.12.909. Subsequent changes carried by this release are documented under Unreleased in CHANGELOG.md.

## What changes

- **Guard reports a new dependency that runs a script on install (#6335).** The collector reads each active project's `package-lock.json` and records the packages that npm marks `hasInstallScript`. The first read is a baseline. When a later read shows a newly marked package, each session in that directory gets an "Install scripts" finding that names the package and its version. The finding is a warning, and critical when the installed package's script pipes a download to a shell, decodes a blob, reads a credential file or reads a publishing token. Switching a Guard check off now also silences the findings that come from the inventory.
- **One event with unencodable text no longer stops later events from being stored (#6313).** An event that carried a lone surrogate made every flush of the event queue fail, so later events stayed in memory. The store now rewrites the text of the queued events once (a lone surrogate becomes U+FFFD) and writes them again.
- **A failing pre-tool hook is reported when tool replies arrive as user messages (#6321).** The check for an agent blocked by an erroring hook read a `user` message holding `tool_result` blocks as a user turn and started its count again. It now reads each block as a tool reply.

## Verification and limits

- #6335: 7 new tests and two red-team corpus cases. On one working machine, 844 project directories with a lockfile raise nothing at rest. npm lockfiles version 2 and 3 only. A project whose first install is the poisoned one has no baseline and is not reported.
- #6313: 6 new tests, 5 of which fail without the fix. Only the event queue is covered.
- #6321: 4 new tests, 2 of which fail without the fix. Not run against a live session with a failing hook.

None of the three adds an HTTP route, so the cloud pin needs no new route-policy entry. Package versioning and tagging remain owned by the release workflow.
