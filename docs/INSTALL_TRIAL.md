# Fresh-install trial protocol

A machine check and a person check are different things, and only one of them
can be automated.

`scripts/verify_published_wheel.py` (run cross-platform by
`.github/workflows/verify-published-wheel.yml`) proves the published wheel
**installs and runs**: the right version resolves, the dashboard serves, a
machine with no agent data gets an explanation, it starts with the network
blocked, and uninstall leaves nothing behind. If that is green, mechanical
failure is largely ruled out.

It cannot tell you whether a person who did not build this reaches something
useful. That is what this protocol is for, and it needs real people.

## The gate

**Five people. At least four reach a real session with no help from you.**

Five is enough to find the blocking bug and nowhere near enough to estimate a
rate — so record it as a usability gate that passed or failed, never as "80%
of users succeed".

## Choosing the five

Cover the axes that have actually broken before, not five copies of the same
machine:

| Axis | Why |
|---|---|
| macOS **and** Linux **and** Windows | Different session paths, different permission models. Windows has had a 5-week silent CLI regression. |
| At least two on **Claude Code or Codex** | Not only OpenClaw. These are the runtimes most readers have, and they are the ones behind the paid adapter. |
| At least one on a machine with **no agent history** | The empty-state path. It is the first screen a curious reader sees. |
| At least one who has **never heard of the project** | Someone who already knows what it does cannot see what the first screen fails to say. |

## Running one trial

Send exactly this, and then say nothing else until they are done:

> Install this and tell me what you see. Nothing else — I want to know where
> you get stuck.
> `pip install clawmetry && clawmetry`
> https://github.com/vivekchand/clawmetry

**Do not help.** The whole value is in what they do when they are stuck. If you
answer a question, that trial is over — record it as a failure with the
question they asked, because a reader on Hacker News will hit the same wall
with nobody to ask.

Watch for, and write down verbatim:

- the first moment they hesitate, and what they were looking at;
- anything they say out loud that begins "wait" or "is this…";
- whether they find what is free without being told;
- whether they ever see a real session, or give up first;
- what they think it is for, in their own words, at the end.

## Recording a trial

Copy this block per person. Keep the verbatim quotes; the paraphrase is where
the finding gets lost.

```
Tester:            (initials / role, not name)
OS + Python:
Runtimes present:
Started at:                        Reached a real session at:            [or: never]
Needed rescue:     yes / no        If yes, the question they asked:

First hesitation (what was on screen, what they said):

Did they work out what is free, unprompted?   yes / no / did not look

What they said it was for, at the end (verbatim):

Blocker(s) hit:
  - [ ] issue filed:              owner:
```

## After the five

1. Anything that blocked **two or more people** is fixed before the trials
   count as passed. One person hitting a wall is a data point; two is the
   product.
2. Every other failure gets an issue with an owner and either a fix or a
   documented workaround.
3. Record the outcome as a gate: **passed** (≥4 of 5 unaided) or **failed**,
   plus the list of blockers. Not a percentage.

If four of five got there and the two blockers are filed and owned, the
usability gate is closed. If three did, it is not — and shipping anyway means
choosing to find out from strangers instead.
