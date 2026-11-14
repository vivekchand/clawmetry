"""Trust only direct requests addressed to a loopback host."""

LOOPBACK_ADDRS = frozenset({"127.0.0.1", "::1", "localhost"})


def is_direct_loopback_request(req):
    """A local socket peer alone does not establish trust (DNS rebinding).

    Read the raw peer and Host rather than forwarded values. Proxied callers
    must authenticate even when the reverse proxy connects over loopback.
    """
    if (req.environ.get("REMOTE_ADDR") or "").strip().lower() not in LOOPBACK_ADDRS:
        return False
    host = (req.headers.get("Host") or "").strip().lower()
    if host.startswith("["):
        end = host.find("]")
        if end == -1:
            return False
        suffix = host[end + 1:]
        if suffix and (not suffix.startswith(":") or not suffix[1:].isdigit()):
            return False
        host = host[:end + 1]
    elif ":" in host:
        host, port = host.rsplit(":", 1)
        if not port.isdigit():
            return False
    if host not in {"localhost", "127.0.0.1", "[::1]"}:
        return False
    return not any(name in req.headers for name in ("X-Forwarded-For", "X-Real-IP", "Forwarded"))
