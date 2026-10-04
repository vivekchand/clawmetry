# Hosted Assistant release

The hosted dashboard previously disabled Assistant even when a connected node could run the local Assistant. This release carries #6330 and uses that same node executor through the paired encrypted cloud relay.

## What changes

- Ask questions, stream real replies and view query-backed charts from the hosted dashboard. Requests and results stay encrypted between the browser and the node.
- Reopen conversations and save charts to Home. The node owns completed history and panels; local JSON callers retain their response contract.
- Share a bounded executor across local and hosted requests. Cancellation, lease expiry and daemon restarts cannot silently repeat paid work, and incomplete answers are not saved as completed conversations.
- Keep key, node, offline and busy states recoverable and clear decrypted content when the selected connection changes. Improve's Refresh button follows the dashboard theme.

## Verification and rollout

The expanded Assistant/Setup/Improve suite passed 341 checks locally, with two native-Windows skips. Required Windows CI verified cancellation with real process trees. Real local-node browser checks verified text arriving before completion, chart and evidence rendering, concurrent status, saved conversation history, explicit Save to Home, a fresh Home reload, and Stop terminating the owned provider without saving a cancelled conversation.

Hosted execution requires the paired encrypted relay in `vivekchand/clawmetry-cloud#2578`. The release owner must verify the official PyPI wheel against the 23-file manifest from the audited merged release base before the cloud owner adopts its automated pin. Package versioning and tagging remain owned by the release workflow.

The release was rebased onto `1cd9992c4d`, including the runtime audit through `9435991150820c6cb83c7f56b424bb64eb70996d` and subsequent Windows test-dependency documentation only. The only upstream change among those 23 runtime files is `clawmetry/sync.py`: collector project assignment runs on the existing alert tick and adds its helper. Assistant code is unchanged. The 62 project-attribution, detector and pip-install-ratchet checks passed after that rebase.
