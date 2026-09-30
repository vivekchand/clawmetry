"""Calendar-period usage for hosted runtime filters, from one rollup read."""


def runtime_periods(rows, today, week_start, month_start):
    """Use the same local-day boundaries and billing scope as /api/usage."""
    import dashboard

    result = {}
    for row in rows:
        day = str(row.get('day') or '')[:10]
        runtime = str(row.get('runtime') or 'openclaw')
        if not day or day > today:
            continue
        bucket = result.setdefault(runtime, {
            'today': 0, 'week': 0, 'month': 0,
            'todayCost': 0.0, 'weekCost': 0.0, 'monthCost': 0.0,
        })
        for period, start in (('today', today), ('week', week_start), ('month', month_start)):
            if day >= start:
                bucket[period] += int(row.get('tokens') or 0)
                bucket[period + 'Cost'] += float(row.get('cost_usd') or 0)
    for runtime, bucket in result.items():
        for period in ('today', 'week', 'month'):
            bucket[period + 'Cost'] = round(bucket[period + 'Cost'], 6)
        bucket['billingCoverage'] = dashboard._get_billing_coverage(
            [], bucket['todayCost'], bucket['weekCost'], bucket['monthCost'],
            runtime=runtime, fallback_all_covered_when_no_models=True)
    return result
