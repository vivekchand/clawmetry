# Hosted Factory publication

Local requirements, blueprint and implementation plan were written before code on 2026-10-15. Initial API creation attempts failed before HTTP because keychain lookup was unavailable for those invocations. No duplicate record was created.

The authenticated Factory editor created requirement a508a5c5-8821-4964-8930-3561b7d02f2b and its automatically connected feature blueprint 706e78ef-e74a-4ced-9f17-68eade47ca94. Both documents were populated with user stories, contracts, non-goals, alternatives, risks and the hardware qualification boundary.

Authenticated API GET verified requirement version 2 with 21 acceptance criteria, and blueprint version 1 with the full design. The records link to each other. Exact hosted requirement text is in hosted-requirements.json; docs/acceptance_criteria.json mirrors all 21 criterion IDs and texts from that response. Publication is verified; this does not constitute native Drift approval or physical qualification.

After native review, the authenticated editor clarified the six questioned runtime boundaries without weakening acceptance criteria. API GET verified blueprint version 2, updated 2026-10-15T20:47:31.888526, with seven component blocks, exact proxy method names, explicit live entry points, real thread lifecycle, direct writer-owned snapshot generation and observation-owned joint names. blueprint.md mirrors that persisted response. Native review on the previous PR head remains red until a fresh native check passes.
