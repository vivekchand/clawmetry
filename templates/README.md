# templates/

Jinja2 HTML templates loaded by Flask via the auto-configured `template_folder`.
Currently empty — the full dashboard is still rendered from the embedded
`DASHBOARD_HTML` string in `dashboard.py` via `render_template_string`.

Phase 7.3 scaffolding for the per-tab HTML split:
- `tabs/*.html`      — per-tab containers (overview, flow, brain, …)
- `partials/*.html`  — shared UI (modals, onboarding, footer, secret-key)
- `dashboard.html`   — top-level layout once we pivot from string to file
