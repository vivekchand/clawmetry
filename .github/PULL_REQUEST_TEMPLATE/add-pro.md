---
name: 'Pro extension / migration'
about: PRs that add or migrate paid/enterprise code to clawmetry-pro
---

### Summary
Brief description of what is being moved/added and reason.

### Files moved/added
- List of files or modules moved into `clawmetry-pro/`.

### Checklist
- [ ] Entitlement API implemented in OSS and unit-tested (entitlements.*)
- [ ] OSS builds/tests pass without clawmetry-pro installed
- [ ] Mock pro implementation added for CI smoke tests
- [ ] Documentation updated (FLYWHEEL.md, MIGRATION_CHECKLIST.md)
- [ ] Security checklist completed (no secrets, sanitized examples)
- [ ] Release plan & packaging notes included

### Testing
Describe manual and automated tests performed.

### Reviewers
- @team-security (security review)
- @team-platform (release/packaging)

