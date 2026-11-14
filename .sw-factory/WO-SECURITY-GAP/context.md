# Security gap execution context

- Work Order: WO-SECURITY-GAP (local task record; no separate Factory ticket requested)
- Goal: bridge the security detection and enforcement gaps from the Arora post review.
- Current baseline: origin/main 9425e2dd90. Shared root checkout is stale and dirty; edits stay isolated.
- Status: in_review; source approved, release and live verification pending
- Requirement: [Guard security boundaries and timely incident handling](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/96f8c30c-8789-49e8-8ebf-2a36536094a9)
- Feature Blueprint: https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/59a8102e-bfdd-40e2-b66c-25af7b01b333
- Component Blueprint: https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/blueprints/75438bcb-3656-4417-a5e7-2501220da407
- Referenced Blueprint: Guard authority, containment and evidence, 0f695665-f632-4604-b0fb-ea4fdea1732a (complete identity and security-priority contracts)
- Referenced Requirement: Guard authority, containment and evidence, 576aeae0-f9dc-44d3-b91d-04ad4454f000
- Source workflow: AGENTS.md, FLYWHEEL.md, CLAUDE.md, software-factory execution skill.
- New Factory requirement created before product edits. Component blueprint and implementation plan preceded product edits.
- Existing features retained: runtime pre-tool gates, secret-value scanning, same-command upload detection, injection detector, workspace inventory, scanner SARIF/provenance.
- Branch: feat/agent-security-gap
- Cloud delivery: https://github.com/vivekchand/clawmetry-cloud/pull/2666; OSS delivery: https://github.com/vivekchand/clawmetry/pull/6530

- Native proof: real Claude Code and Copilot protected-write denials with ordinary allowed work; a real Claude boundary call ingested as eight events and one durable security finding, inspected in Guard history and investigation.
- Cursor native proof remains unavailable because the CLI requires authentication. No native sandbox or arbitrary-process network containment was established. Guard scanner coverage remains unknown; the existing PR provenance/SARIF workflow remains the independent code-review path.
