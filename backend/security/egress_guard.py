"""Deny-by-default egress check for every outbound HTTP call the pipeline makes.

The original egress_monitor only *labels* events. This guard is enforced: model
clients call `check_url` before opening a connection, and a host that is not on
the allowlist raises `EgressBlocked` instead of sending anything. Every decision
is still recorded in the existing egress monitor so the UI telemetry keeps working.
"""
from __future__ import annotations

from urllib.parse import urlparse

from backend.config import settings
from backend.security.egress_monitor import egress_monitor


class EgressBlocked(RuntimeError):
    """Raised when code tries to reach a host outside the allowlist."""


def check_url(url: str, purpose: str, allowlist: tuple[str, ...] | None = None) -> None:
    host = (urlparse(url).hostname or "").lower()
    allowed = allowlist if allowlist is not None else settings.egress_allowlist
    if host in {h.lower() for h in allowed}:
        egress_monitor.record_event(f"LOCAL:{host}", purpose, "ALLOWED", url)
        return
    egress_monitor.record_event(host or url, purpose, "BLOCKED", f"Refused non-allowlisted host for {purpose}")
    raise EgressBlocked(f"Egress to '{host}' refused (allowlist: {', '.join(allowed)})")
