"""Question-set approvals — decisions beyond yes/no (WO-52, phase 1).

Approvals were strictly binary (approve/deny). Claude Code's
``AskUserQuestion`` tool carries a structured question set — 1-4 questions,
each with a short ``header``, 2-4 labelled ``options`` and an optional
``multiSelect`` flag — and its PreToolUse hook is allowed to answer with
``hookSpecificOutput.updatedInput`` = the original ``tool_input`` plus
``answers: {"<question text>": "<option label>"}`` (a list of labels for
multiSelect questions); the session then resumes with those answers as if
the human had picked them in the terminal.

This module is the shared vocabulary for that flow:

* the hook receiver (``routes/hooks.py``) sanitizes and parks the set,
* the decision walls (``routes/policy.py`` ``/api/approvals/<id>/decide``
  and ``routes/hitl.py`` ``/api/hitl/decide``) validate structured answers
  against the stored set and flip the row,
* the receiver merges the winning answers back into the tool input.

Storage is migration-free: everything rides in the approvals row's ``args``
BLOB under namespaced keys (the ``_cm_risk`` precedent):

  ``args["_cm_questions"]`` — the sanitized question set (list of dicts:
      ``question`` / ``header`` / ``options: [{label, description}]`` /
      ``multiSelect`` / optional ``allow_free_text``).
  ``args["_cm_answers"]``   — the structured answers map, written by the
      decision wall immediately BEFORE it flips the row to
      ``decision='answered'`` (status ``answered``), so a hook waiting on
      the row never observes the answered status without the answers.

Validation is strict by design: an answered question must exist in the
stored set and every selected label must be one of that question's option
labels — unless the question itself carries a truthy free-text flag
(``allow_free_text`` / ``allowFreeText``), in which case any non-empty
string is accepted ("a free-text input when the question set says so").

Safety contract (mirrors the receiver's): a question-set approval that
expires or fails NEVER fabricates or defaults an answer and never follows
the binary ``on_timeout=deny`` default — the fallback is always ``ask``,
i.e. the runtime's own terminal prompt, exactly today's behaviour.
"""
from __future__ import annotations

MAX_QUESTIONS = 4
MAX_OPTIONS = 4

_FREE_TEXT_KEYS = ("allow_free_text", "allowFreeText", "free_text",
                   "freeText", "allowOther")


def _free_text_allowed(question: dict) -> bool:
    return any(bool(question.get(k)) for k in _FREE_TEXT_KEYS)


def sanitize_question_set(tool_input) -> "list[dict] | None":
    """Normalise an AskUserQuestion ``tool_input`` into the stored shape.

    Returns a list of clean question dicts, or ``None`` when the payload
    carries nothing usable (the caller then answers ``ask`` — the terminal
    prompt handles whatever we could not understand). Lenient on extras,
    strict on shape: unknown keys are dropped, questions without text are
    skipped, options are capped at ``MAX_OPTIONS`` with non-string /
    unlabelled entries discarded.
    """
    if not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("questions")
    if not isinstance(raw, list) or not raw:
        return None
    out: list[dict] = []
    for q in raw[:MAX_QUESTIONS]:
        if not isinstance(q, dict):
            continue
        text = str(q.get("question") or "").strip()
        if not text:
            continue
        options: list[dict] = []
        raw_opts = q.get("options")
        if isinstance(raw_opts, list):
            for o in raw_opts[:MAX_OPTIONS]:
                if isinstance(o, dict):
                    label = str(o.get("label") or "").strip()
                    if not label:
                        continue
                    options.append({
                        "label": label,
                        "description": str(o.get("description") or ""),
                    })
                elif isinstance(o, str) and o.strip():
                    options.append({"label": o.strip(), "description": ""})
        entry = {
            "question": text,
            "header": str(q.get("header") or "").strip(),
            "options": options,
            "multiSelect": bool(q.get("multiSelect")),
        }
        if _free_text_allowed(q):
            entry["allow_free_text"] = True
        out.append(entry)
    return out or None


def question_summary(questions: list) -> str:
    """One-line preview for the row's ``action`` string and pending chip."""
    heads = []
    for q in questions or []:
        if not isinstance(q, dict):
            continue
        head = str(q.get("header") or q.get("question") or "").strip()
        if head:
            heads.append(head[:40])
    n = len(questions or [])
    label = "question" if n == 1 else "questions"
    return f"{n} {label}" + (f" — {'; '.join(heads)}" if heads else "")


def validate_answers(questions, answers) -> "str | None":
    """Validate a structured answers map against the stored question set.

    Returns an error string (the decision wall turns it into a 400), or
    ``None`` when the answers are acceptable. Rules:

    * ``answers`` must be a non-empty object keyed by question text;
    * every answered question must exist in the stored set;
    * a single-choice question takes one string; a multiSelect question
      takes a string or a non-empty list of strings;
    * every selected label must exist among that question's options,
      unless the question allows free text.

    Partial answer maps are allowed (only what is answered is validated) —
    the UI enforces completeness before submitting; the wall enforces
    correctness of what arrives.
    """
    if not isinstance(questions, list) or not questions:
        return "no stored question set to validate against"
    if not isinstance(answers, dict) or not answers:
        return "answers must be a non-empty object keyed by question text"
    by_text = {str(q.get("question")): q for q in questions
               if isinstance(q, dict) and q.get("question")}
    for qtext, value in answers.items():
        q = by_text.get(str(qtext))
        if q is None:
            return f"unknown question: {str(qtext)[:80]!r}"
        labels = {o.get("label") for o in (q.get("options") or [])
                  if isinstance(o, dict) and o.get("label")}
        free = _free_text_allowed(q)
        if isinstance(value, list):
            if not q.get("multiSelect"):
                return (f"question {str(qtext)[:60]!r} is single-choice — "
                        "the answer must be a string, not a list")
            if not value:
                return f"question {str(qtext)[:60]!r}: empty selection"
            picked = value
        else:
            picked = [value]
        for label in picked:
            if not isinstance(label, str) or not label.strip():
                return (f"question {str(qtext)[:60]!r}: every answer must "
                        "be a non-empty string")
            if label not in labels and not free:
                return (f"unknown option {label[:60]!r} for question "
                        f"{str(qtext)[:60]!r}")
    return None


def merge_answers_into_input(tool_input, answers) -> dict:
    """The ``updatedInput`` the hook replies with: original tool input plus
    the ``answers`` map (labels as strings, multiSelect as lists)."""
    merged = dict(tool_input) if isinstance(tool_input, dict) else {}
    merged["answers"] = {
        str(k): (list(v) if isinstance(v, list) else str(v))
        for k, v in dict(answers).items()
    }
    return merged


def answers_summary(questions, answers) -> str:
    """Human-readable one-liner for ``decision_reason`` / audit log."""
    parts = []
    for q in questions or []:
        if not isinstance(q, dict):
            continue
        value = (answers or {}).get(q.get("question"))
        if value is None:
            continue
        head = str(q.get("header") or q.get("question") or "").strip()[:40]
        text = ", ".join(str(v) for v in value) if isinstance(value, list) \
            else str(value)
        parts.append(f"{head}: {text[:80]}" if head else text[:80])
    return ("answered — " + "; ".join(parts))[:290] if parts else "answered"


def apply_answer_decision(approval_id, row, answers, *, resolver,
                          reason, write) -> "tuple[bool, str, int]":
    """Shared decision-wall core for ``decision='answer'``.

    ``write(method_name, **kwargs) -> bool`` is the caller's store writer
    (daemon-proxy first — e.g. ``routes.hooks._ls_write``). Returns
    ``(ok, status_or_error, http_code)``.

    Write order matters: the answers are merged into ``args`` while the row
    is still pending, and only then is the row flipped to ``answered`` via
    ``update_approval_decision`` (first-click-wins). A hook polling the row
    therefore never sees the answered status without ``_cm_answers``. The
    flip only ever transitions a *pending* row, so a racing binary decision
    keeps its result; callers re-read the row afterwards to report what
    actually stands.
    """
    args = row.get("args") if isinstance(row.get("args"), dict) else {}
    questions = args.get("_cm_questions")
    if not isinstance(questions, list) or not questions:
        return (False,
                "not a question-set approval (no stored question set)", 400)
    err = validate_answers(questions, answers)
    if err:
        return False, err, 400
    merged = dict(args)
    merged["_cm_answers"] = {
        str(k): (list(v) if isinstance(v, list) else str(v))
        for k, v in answers.items()
    }
    # Answers land in args BEFORE the status flips (see docstring). The
    # upsert re-states the pre-checked 'pending' status; the authoritative
    # transition is the update_approval_decision below.
    if not write("ingest_approval", approval={
            "id": str(approval_id), "args": merged, "status": "pending"}):
        return False, "answer write failed (approval store unavailable)", 500
    summary = str(reason or answers_summary(questions, answers))[:300]
    write("update_approval_decision", approval_id=str(approval_id),
          decision="answered", resolver=resolver, reason=summary)
    return True, "answered", 200
