#!/usr/bin/env python3
"""Work Order CLI for the 8090 Software Factory board.

Usage:
  python3 .claude/wo.py list                 # full board, sorted by pick order
  python3 .claude/wo.py pick [n]             # next n work orders to execute
  python3 .claude/wo.py show <number>        # full markdown + linked context
  python3 .claude/wo.py status <number> <backlog|ready|in_progress|in_review|blocked|completed>
  python3 .claude/wo.py comment <number> <path-to-markdown-file>
  python3 .claude/wo.py ledger              # what the loop has already attempted
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_client import call  # noqa: E402

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wo_ledger.json")

# Lower sorts first. in_review work is nearly done, so it drains before new builds.
STATUS_RANK = {
    "in_review": 0,
    "in_progress": 1,
    "ready": 2,
    "backlog": 3,
    "blocked": 8,
    "completed": 9,
}
PRIORITY_RANK = {"urgent": 0, "high": 1, "medium": 2, "low": 3, None: 4}


def board():
    rows, page = [], 1
    while True:
        r = call("GET", "/work_orders", params={"page": page, "page_size": 100})
        items = r.get("items") or []
        rows += items
        if len(items) < 100:
            return rows
        page += 1


def ledger():
    try:
        return json.load(open(LEDGER))
    except Exception:
        return {}


def ledger_write(number, entry):
    d = ledger()
    d[str(number)] = entry
    json.dump(d, open(LEDGER, "w"), indent=1, sort_keys=True)


def sort_key(w):
    return (
        STATUS_RANK.get(w.get("status"), 5),
        PRIORITY_RANK.get(w.get("priority"), 4),
        w.get("work_order_number", 0),
    )


def by_number(n):
    return call("GET", f"/work_orders/by_number/{n}").get("data") or {}


def cmd_list():
    for w in sorted(board(), key=sort_key):
        mark = " [attempted]" if str(w["work_order_number"]) in ledger() else ""
        print(f"#{w['work_order_number']:<4} {w['status']:<12} {str(w.get('priority')):<7} "
              f"{w.get('type',''):<13} {w['title'][:80]}{mark}")


def cmd_pick(n=1):
    done = ledger()
    out = []
    for w in sorted(board(), key=sort_key):
        if w["status"] in ("completed", "blocked"):
            continue
        e = done.get(str(w["work_order_number"]))
        if e and e.get("state") in ("shipped", "gave_up"):
            continue
        out.append(w)
        if len(out) >= n:
            break
    print(json.dumps([{"number": w["work_order_number"], "status": w["status"],
                       "priority": w.get("priority"), "type": w.get("type"),
                       "title": w["title"]} for w in out], indent=1))


def cmd_show(n):
    d = by_number(n)
    print(f"# WO-{n}: {d.get('title')}")
    print(f"status={d.get('status')} priority={d.get('priority')} type={d.get('type')} "
          f"created={d.get('created_at')} updated={d.get('updated_at')}")
    print(f"connectedContext={json.dumps(d.get('connectedContext'))}")
    print("\n" + (d.get("markdown_content") or "(no description)"))
    c = call("GET", f"/work_orders/{d['id']}/comments")
    for item in (c.get("items") or []):
        print(f"\n--- comment by {(item.get('author') or {}).get('name')} "
              f"{item.get('created_at')} ---\n{item.get('markdown_content','')[:1500]}")


def cmd_status(n, status):
    d = by_number(n)
    r = call("POST", "/work_orders/batch_update", body={
        "request_id": f"wo-loop-{n}-{status}",
        "operations": [{
            "operation_id": f"op-{n}",
            "operation_type": "UpdateStatus",
            "target": {"work_order_id": d["id"]},
            "patch": {"status": status},
        }],
    })
    print(json.dumps(r, indent=1)[:1500])


def cmd_comment(n, path):
    d = by_number(n)
    md = open(path).read()
    r = call("POST", f"/work_orders/{d['id']}/comments", body={"markdown_content": md})
    print(json.dumps(r, indent=1)[:800])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        cmd_list()
    elif cmd == "pick":
        cmd_pick(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    elif cmd == "show":
        cmd_show(sys.argv[2])
    elif cmd == "status":
        cmd_status(sys.argv[2], sys.argv[3])
    elif cmd == "comment":
        cmd_comment(sys.argv[2], sys.argv[3])
    elif cmd == "ledger":
        print(json.dumps(ledger(), indent=1))
    else:
        print(__doc__)
