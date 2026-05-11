# Slack Emoji-React Approvals — Design Proposal

**Status:** proposal • **Effort:** 4–6 engineering days • **Owner:** TBD
**Author:** Claude / staff-engineer mode • **Date:** 2026-04-25

---

## TL;DR

Approvals today are a **scary red dashboard button.** Make them a **collaborative
Slack thread.** When a risky action needs approval, post one Slack message to a
`#claw-approvals` channel — team members react with 👍 to approve, 🚫 to deny.
The reaction round-trips back to ClawMetry, the agent unblocks, and the Slack
thread becomes the audit trail.

This is a "gateway" feature for non-technical buyers (CFO, CISO, ops team).
The Approvals tab today says nothing about the *humans* on the other side.
Slack says everything.

---

## Why this is the right next bet

1. **Already 80% there.** Cloud has Slack webhook delivery
   (`routes/cloud.py:_notify_slack`) that posts approval messages with
   Approve/Deny URL buttons. We just need the round-trip.
2. **High-leverage feature gap.** Linear, Vercel, and Anthropic's own gateway
   all use Slack-native approval workflows for high-stakes actions. No serious
   buyer signs up to ClawMetry without it.
3. **Conversion-driving.** Per the audit, the channels-and-approvals UX is
   the #1 trust gap. A Slack thread with 👍 reactions feels like a real
   *team* product instead of a hobby dashboard.
4. **No new infrastructure.** Reuses existing Slack webhook setup; adds one
   new endpoint + one new DB table + one new Slack OAuth app.

---

## User flow

### 1. Setup (one-time, per workspace)
- User clicks **"Connect Slack"** in **Notifications** tab → Slack OAuth flow
- We request scopes: `chat:write`, `reactions:read`, `channels:history` on
  one channel (default `#claw-approvals`, configurable)
- Save `bot_token`, `team_id`, `channel_id` against the user's account
- Show a sample test message in the channel: *"✅ Connected. Approvals from
  ClawMetry will appear here."*

### 2. An approval fires
- Agent tries a risky action (e.g. `rm -rf` on a non-allowlisted path)
- ClawMetry policy engine pauses the action, creates an approval record
- Cloud calls Slack `chat.postMessage` with:
  - **Title:** "🛡️ Approval needed for `exec` on `agent+vivek-Mac`"
  - **Context:** policy name, command preview, who triggered it (channel/user)
  - **Footer:** _"React 👍 to approve · 🚫 to deny · 💬 reply for context"_
- Save `slack_ts` (message timestamp) into the approval record so we know
  which approval the reaction maps to

### 3. Team member reacts
- Slack pushes `reaction_added` event to our webhook (`/api/slack/events`)
- Our handler:
  - Verifies signature (`X-Slack-Signature` HMAC, prevent spoofing)
  - Looks up `(team_id, channel_id, message_ts)` → approval record
  - If 👍: `approval.status = 'approved'`, `approved_by = slack_user_id`
  - If 🚫: `approval.status = 'denied'`, `denied_by = slack_user_id`
  - Existing OSS approvals daemon picks up the status change on its next
    poll and unblocks/rejects the action — **no new logic needed downstream**
  - Edit the original Slack message to add: _"✅ Approved by @vivek (3h ago)"_
    or _"🚫 Denied by @kody (12s ago)"_

### 4. The audit trail
- Slack thread auto-becomes the audit trail: who approved, when, any
  threaded discussion ("can you check what dir this is?")
- ClawMetry's Approvals tab cross-links to the Slack thread for each
  resolved approval
- Compliance-friendly: SOC 2 auditors love "approval log lives in Slack
  with timestamps and reactor identity"

---

## What we build

### Backend

**1. New table** `slack_approval_threads`:
```sql
CREATE TABLE slack_approval_threads (
  approval_id    TEXT PRIMARY KEY REFERENCES approvals(id),
  team_id        TEXT NOT NULL,
  channel_id     TEXT NOT NULL,
  message_ts     TEXT NOT NULL,
  posted_at      TIMESTAMPTZ DEFAULT NOW(),
  resolved_by    TEXT,           -- Slack user_id who reacted first
  resolved_at    TIMESTAMPTZ
);
CREATE INDEX idx_slack_thread_lookup ON slack_approval_threads(team_id, channel_id, message_ts);
```

**2. New endpoint** `/api/slack/events` (cloud):
- Verify Slack signature (HMAC-SHA256 of timestamp + body, secret from env)
- Handle `url_verification` challenge for first-time setup
- Handle `event_callback` with `reaction_added` payload
- Look up approval, mutate status, edit message via `chat.update`

**3. New endpoint** `/api/cloud/slack/oauth/callback`:
- Exchange OAuth code for bot token via `oauth.v2.access`
- Save `bot_token`, `team_id`, `channel_id` against user's account
- Redirect back to Notifications tab with success state

**4. Modify** `_notify_slack()` in `routes/cloud.py`:
- After posting, capture the response `ts` and write
  `slack_approval_threads` row
- Use `chat.postMessage` (with bot token) instead of webhook URL so we
  can edit the message later

### Frontend

**5. Notifications tab card**: replace the existing "Slack Webhook URL" form
   with a "Connect Slack" OAuth button when the user has no `bot_token`.
   Once connected, show: _"Connected to #claw-approvals · 12 approvals routed
   this month · [Test] · [Disconnect]"_

**6. Approvals tab**: add a "💬 Slack" pill on each approval row that links
   to the message permalink. Resolved approvals show the reactor's name +
   timestamp.

### Ops

**7. Slack app manifest**: register a Slack app at api.slack.com with:
   - OAuth scopes: `chat:write`, `chat:write.public`, `reactions:read`,
     `channels:read`, `channels:history`
   - Event subscriptions: `reaction_added` → our webhook URL
   - Slash commands (optional v2): `/claw status`, `/claw history`
   - Distribution: public install (every customer can install our app
     into their Slack workspace)

**8. Secrets**: `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET`
   in Cloud Run env (same pattern as `STRIPE_*`).

---

## Effort breakdown (4–6 days)

| Day | Task |
|---|---|
| 1   | Slack app registration + OAuth callback + bot_token persistence |
| 2   | Modify _notify_slack to use chat.postMessage + persist message_ts |
| 3   | /api/slack/events handler with signature verification + reaction round-trip |
| 4   | chat.update message edit + approvals daemon integration test |
| 5   | Frontend: Notifications "Connect Slack" + Approvals "💬 Slack" pill |
| 6   | E2E test, docs, Slack app store submission, internal dogfood |

---

## Edge cases worth handling

- **Multiple reactions race**: first reactor wins. Subsequent reactors are
  no-ops; we just edit the message to mention them in the audit log.
- **Reactor isn't a team member**: deny if Slack user_id isn't in the
  workspace's allowlist (configurable per approval rule).
- **Approval times out**: if no reaction in N minutes, post a follow-up
  ping (`@here approval still pending — agent waiting`).
- **Bot kicked from channel**: detect on next post (Slack returns `not_in_channel`),
  surface a fix-it banner in the Notifications tab.
- **Token revoked**: re-auth flow if Slack returns `invalid_auth`.

---

## Why NOT to ship this today

This is **6 engineering days**, not a 30-minute polish PR. It needs:
1. Slack app registration (1-2 day cycle, requires public-facing legal review)
2. Event-subscription URL must be publicly verifiable HTTPS (already true)
3. SOC 2 review of the new bot_token storage (same risk class as Stripe key)

The polish PRs we shipped today (Storage / Network / Skills / TTS / trial
banner / cost optimizer accuracy / icon placeholders / channel status /
billing demotion fix) all directly fix what the user can SEE today. Slack
emoji-approvals is the next big bet, not the next quick win.

---

## Recommended next steps after merging today's polish

1. **This week**: Build a one-customer dogfood Slack app (no public store
   listing yet) — confirms the round-trip works in production with a real
   Slack workspace.
2. **Week 2**: Polish UX, write Slack app store listing, submit for review.
3. **Week 3**: Public launch with a "Slack approvals" feature blog post —
   this is exactly the kind of "wait, the dashboard talks back to Slack?"
   moment that drives word-of-mouth signups.

— Generated by Claude (staff engineer mode)
