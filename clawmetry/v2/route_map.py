"""Canonical tab-name mapping between v1 and v2 URL schemes.

V1_TO_V2 maps the short tab identifiers used in v1 URL fragments /
query params to the corresponding v2 React Router path segments.
V2_TO_V1 is the reverse.

Usage::

    from clawmetry.v2.route_map import V1_TO_V2, V2_TO_V1
    v2_tab = V1_TO_V2.get(v1_tab, v1_tab)  # graceful passthrough for unmapped tabs
    v1_tab = V2_TO_V1.get(v2_tab, v2_tab)
"""

V1_TO_V2: dict[str, str] = {
    "flow": "trace",
    "sessions": "brain",
    "memory": "context",
    "usage": "cost",
    "crons": "ops",
    "logs": "ops",
}

# Reverse mapping. "crons" and "logs" both map to "ops" in V1_TO_V2,
# so V2_TO_V1["ops"] resolves to "logs" (last writer wins in dict
# comprehension). Callers that need to distinguish should consult
# V1_TO_V2 directly rather than relying on V2_TO_V1["ops"].
V2_TO_V1: dict[str, str] = {v: k for k, v in V1_TO_V2.items()}
