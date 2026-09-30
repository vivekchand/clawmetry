"""Current usage-value alerts from one cached, bounded daily-rollup read."""
from datetime import date, timedelta
import logging
import math
import threading
import time

_log = logging.getLogger(__name__)
_lock = threading.Lock()
_cache = (None, 0.0, None)


def _read_days(start, end):
    from routes.local_query import local_store_via_daemon
    rows = local_store_via_daemon('query_rollup_runtime_daily', since=start, until=end)
    if rows is None:
        from clawmetry.local_store import get_store
        rows = get_store(read_only=True).query_rollup_runtime_daily(since=start, until=end)
    return rows


def current():
    """Revalidate at most once a minute, immediately after local midnight."""
    global _cache
    today = date.today()
    with _lock:
        if _cache[0] == today and time.monotonic() < _cache[1]:
            return _cache[2]
        result = None
        try:
            start, end = (today - timedelta(days=7)).isoformat(), today.isoformat()
            daily = total = 0.0
            for row in _read_days(start, end) or []:
                day = str(row.get('day') or '')
                value = float(row.get('cost_usd') or 0)
                if not math.isfinite(value) or value < 0 or not start <= day <= end:
                    continue
                if day == end:
                    daily += value
                else:
                    total += value
            average = total / 7
            if average > 0 and daily > average * 2:
                ratio = daily / average
                result = {'daily': daily, 'average': average, 'ratio': ratio,
                    'message': f'Usage-value anomaly (all runtimes): today ${daily:.2f} is '
                    f'{ratio:.1f}x the previous 7-day average (${average:.2f}/day). '
                    'Estimated at published rates, not a bill.'}
        except Exception:
            _log.warning('Could not revalidate usage-value anomaly', exc_info=True)
        _cache = (today, time.monotonic() + 60, result)
        return result


def refresh_active(alerts):
    """Keep historical records untouched; only show a current anomaly once."""
    if not any(a.get('rule_id') == 'anomaly_daily' for a in alerts):
        return alerts
    live = current()
    result = []
    shown = False
    for alert in alerts:
        if alert.get('rule_id') != 'anomaly_daily':
            result.append(alert)
        elif live and not shown:
            result.append(dict(alert, message=live['message']))
            shown = True
    return result
