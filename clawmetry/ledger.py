"""
clawmetry/ledger.py — Local cost tracking and terminal output.

Thread-safe, never throws, sub-millisecond overhead.
"""
from __future__ import annotations

import atexit
import os
import threading
import time
from typing import Dict

# ──────────────────────────────────────────────────────────────────────────────
# ANSI helpers (respect NO_COLOR / non-TTY)
# ──────────────────────────────────────────────────────────────────────────────
_USE_COLOR = os.isatty(1) and os.environ.get("NO_COLOR") is None


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _bold(t: str) -> str:
    return _c("1", t)


def _dim(t: str) -> str:
    return _c("2", t)


def _green(t: str) -> str:
    return _c("32", t)


# ──────────────────────────────────────────────────────────────────────────────
# Ledger state
# ──────────────────────────────────────────────────────────────────────────────

class _Ledger:
    """Single in-process cost ledger. Thread-safe via a fine-grained lock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session_start = time.monotonic()
        self._session_calls = 0
        self._session_cost = 0.0
        # per-provider totals for this session
        self._session_by_provider: Dict[str, float] = {}

        # "today" counters — persisted to ~/.clawmetry/today.json between sessions
        self._today_calls = 0
        self._today_cost = 0.0
        self._today_by_provider: Dict[str, float] = {}

        # cloud sync queue (populated when CLAWMETRY_API_KEY is set)
        self._pending_sync: list = []

        self._load_today()
        atexit.register(self._on_exit)

    # ── persistence ──────────────────────────────────────────────────────────

    def _today_path(self):
        import pathlib
        p = pathlib.Path.home() / ".clawmetry" / "today.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _load_today(self) -> None:
        try:
            import json, datetime
            p = self._today_path()
            if not p.exists():
                return
            data = json.loads(p.read_text())
            today = datetime.date.today().isoformat()
            if data.get("date") != today:
                return  # new day — start fresh
            self._today_calls = int(data.get("calls", 0))
            self._today_cost = float(data.get("cost", 0.0))
            self._today_by_provider = {
                k: float(v) for k, v in data.get("by_provider", {}).items()
            }
        except Exception:
            pass

    def _save_today(self) -> None:
        try:
            import json, datetime
            p = self._today_path()
            data = {
                "date": datetime.date.today().isoformat(),
                "calls": self._today_calls,
                "cost": self._today_cost,
                "by_provider": self._today_by_provider,
            }
            p.write_text(json.dumps(data))
        except Exception:
            pass

    # ── record ────────────────────────────────────────────────────────────────

    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """Record one API call. Called from response hooks — must not throw."""
        try:
            with self._lock:
                self._session_calls += 1
                self._session_cost += cost
                self._session_by_provider[provider] = (
                    self._session_by_provider.get(provider, 0.0) + cost
                )

                self._today_calls += 1
                self._today_cost += cost
                self._today_by_provider[provider] = (
                    self._today_by_provider.get(provider, 0.0) + cost
                )

                # snapshot for terminal print (outside the lock call)
                calls = self._today_calls
                today_cost = self._today_cost
                today_by_prov = dict(self._today_by_provider)

                if os.environ.get("CLAWMETRY_API_KEY"):
                    self._pending_sync.append(
                        {
                            "provider": provider,
                            "model": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost": cost,
                        }
                    )

            self._save_today()
            self._print_live(calls, today_cost, today_by_prov)
            if os.environ.get("CLAWMETRY_API_KEY"):
                self._maybe_cloud_sync()
        except Exception:
            pass

    # ── terminal output ───────────────────────────────────────────────────────

    def _fmt_cost(self, c: float) -> str:
        return f"${c:.2f}"

    def _provider_breakdown(self, by_prov: Dict[str, float]) -> str:
        parts = [
            f"{p}: {self._fmt_cost(v)}"
            for p, v in sorted(by_prov.items(), key=lambda x: -x[1])
        ]
        return " · ".join(parts)

    def _print_live(self, calls: int, today_cost: float, today_by_prov: Dict[str, float]) -> None:
        try:
            breakdown = self._provider_breakdown(today_by_prov)
            prefix = _bold(_green("clawmetry ▸"))
            cost_str = _bold(self._fmt_cost(today_cost))
            calls_str = f"today ({calls} call{'s' if calls != 1 else ''})"
            sep = _dim("──")
            print(f"{prefix} {cost_str} {calls_str} {sep} {breakdown}", flush=True)
        except Exception:
            pass

    # ── atexit ────────────────────────────────────────────────────────────────

    def _on_exit(self) -> None:
        try:
            with self._lock:
                session_cost = self._session_cost
                session_calls = self._session_calls
                session_by_prov = dict(self._session_by_provider)
                today_cost = self._today_cost
                elapsed = time.monotonic() - self._session_start

            if session_calls == 0:
                return  # nothing tracked — stay silent

            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            duration = f"{mins}m {secs}s" if mins else f"{secs}s"

            # Rough monthly estimate from today's spend (extrapolated linearly)
            try:
                import datetime
                now = datetime.datetime.now()
                seconds_today = (
                    now - now.replace(hour=0, minute=0, second=0, microsecond=0)
                ).total_seconds()
                daily_rate = today_cost / max(seconds_today, 1) * 86_400
                monthly_est = daily_rate * 30
            except Exception:
                monthly_est = 0.0

            prefix = _bold(_green("clawmetry ▸"))
            cost_str = _bold(self._fmt_cost(session_cost))
            today_str = _bold(self._fmt_cost(today_cost))
            monthly_str = _bold(f"~{self._fmt_cost(monthly_est)}/mo")
            sep = _dim("──")

            msg = (
                f"{prefix} session: {cost_str} "
                f"({session_calls} call{'s' if session_calls != 1 else ''}, {duration}) "
                f"{sep} today: {today_str} {sep} {monthly_str}"
            )
            print(msg, flush=True)
        except Exception:
            pass

    # ── cloud sync ────────────────────────────────────────────────────────────

    # ── public query API ──────────────────────────────────────────────────────

    def session_total(self) -> dict:
        """Return session-level aggregate stats."""
        with self._lock:
            elapsed = time.monotonic() - self._session_start
            return {
                "total_usd": self._session_cost,
                "calls": self._session_calls,
                "by_provider": dict(self._session_by_provider),
                "duration_seconds": elapsed,
            }

    def today_total(self) -> dict:
        """Return today's aggregate stats."""
        with self._lock:
            return {
                "total_usd": self._today_cost,
                "calls": self._today_calls,
                "by_provider": dict(self._today_by_provider),
            }

    def monthly_estimate(self) -> float:
        """Rough monthly cost estimate extrapolated from today's spend."""
        try:
            import datetime
            now = datetime.datetime.now()
            seconds_today = (
                now - now.replace(hour=0, minute=0, second=0, microsecond=0)
            ).total_seconds()
            with self._lock:
                today_cost = self._today_cost
            daily_rate = today_cost / max(seconds_today, 1) * 86_400
            return daily_rate * 30
        except Exception:
            return 0.0

    # ── cloud sync ────────────────────────────────────────────────────────────

    def _maybe_cloud_sync(self) -> None:
        """Fire-and-forget background sync to cloud dashboard."""
        try:
            import threading as _t

            def _sync():
                try:
                    with self._lock:
                        if not self._pending_sync:
                            return
                        batch = list(self._pending_sync)
                        self._pending_sync.clear()

                    import urllib.request, json as _j, os as _o
                    api_key = _o.environ.get("CLAWMETRY_API_KEY", "")
                    ingest = _o.environ.get(
                        "CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com"
                    )
                    url = ingest.rstrip("/") + "/ingest/llm-calls"
                    body = _j.dumps({"calls": batch}).encode()
                    req = urllib.request.Request(
                        url,
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}",
                        },
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=5)
                except Exception:
                    pass

            _t.Thread(target=_sync, daemon=True).start()
        except Exception:
            pass


# ── singleton ─────────────────────────────────────────────────────────────────

_ledger: "_Ledger | None" = None
_ledger_lock = threading.Lock()


def get_ledger() -> "_Ledger":
    global _ledger
    if _ledger is None:
        with _ledger_lock:
            if _ledger is None:
                _ledger = _Ledger()
    return _ledger
