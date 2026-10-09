"""Outbound network policy – SSRF protection.

Validates any URL that the server will fetch or drive a browser to, before the
outbound connection is made.  DNS resolution is performed so that attacker-
controlled hostnames that resolve to private IPs are also rejected.

Environment variables
---------------------
QA_ALLOW_PRIVATE_TARGETS : "true" | "false"  (default "false")
    Allow RFC-1918 / loopback destinations.  Never enable in production.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Allowed URL schemes
# ---------------------------------------------------------------------------
ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_SCHEMES = {
    "file",
    "ftp",
    "gopher",
    "data",
    "javascript",
    "dict",
    "tftp",
    "ldap",
    "ldaps",
    "sftp",
    "smb",
    "mailto",
    "irc",
}

# ---------------------------------------------------------------------------
# Known cloud-metadata endpoint host literals
# ---------------------------------------------------------------------------
METADATA_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "169.254.170.2",
    "fd00:ec2::254",
}


def _is_private_ip(addr: "ipaddress.IPv4Address | ipaddress.IPv6Address") -> bool:
    """Return True if the address is loopback, private, link-local, etc."""
    return (
        addr.is_loopback
        or addr.is_private
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or addr.is_reserved
    )


def _allow_private_targets() -> bool:
    return os.getenv("QA_ALLOW_PRIVATE_TARGETS", "false").strip().lower() == "true"


def _resolve_addresses(hostname: str) -> list:
    """DNS-resolve hostname to a list of IP address objects.

    Returns empty list on resolution failure (caller decides policy).
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, OSError):
        return []

    addrs = []
    for info in infos:
        raw_ip = info[4][0]
        try:
            addrs.append(ipaddress.ip_address(raw_ip))
        except ValueError:
            pass
    return addrs


class SSRFViolation(ValueError):
    """Raised when a URL violates the outbound network policy."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Outbound URL blocked [{reason}]: {url}")


def validate_url(url: str) -> str:
    """Validate *url* against the outbound network policy.

    Returns the URL unchanged if allowed.
    Raises :class:`SSRFViolation` on any violation.
    Raises :class:`ValueError` if the URL is malformed or empty.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty")

    url = url.strip()
    parsed = urlparse(url)

    scheme = (parsed.scheme or "").lower()
    if not scheme:
        raise SSRFViolation(url, "missing URL scheme")

    if scheme in BLOCKED_SCHEMES:
        raise SSRFViolation(url, f"scheme '{scheme}' is not allowed")

    if scheme not in ALLOWED_SCHEMES:
        raise SSRFViolation(url, f"scheme '{scheme}' is not in the allowed list {sorted(ALLOWED_SCHEMES)!r}")

    hostname = parsed.hostname or ""
    if not hostname:
        raise SSRFViolation(url, "URL has no hostname")

    # Literal metadata host check (before DNS)
    if hostname.lower() in METADATA_HOSTS:
        raise SSRFViolation(url, f"host '{hostname}' is a known metadata endpoint")

    # If hostname is already a literal IP, validate directly without DNS
    try:
        literal_addr = ipaddress.ip_address(hostname)
        metadata_ips = {
            ipaddress.ip_address("169.254.169.254"),
            ipaddress.ip_address("169.254.170.2"),
        }
        if literal_addr in metadata_ips:
            raise SSRFViolation(url, f"IP {hostname} is a known metadata endpoint")

        if not _allow_private_targets() and _is_private_ip(literal_addr):
            raise SSRFViolation(url, f"private/reserved IP address {hostname} is blocked")
        return url
    except ValueError:
        pass  # not a literal IP; continue with DNS resolution

    # DNS resolution – catch CNAME / DNS rebinding tricks
    resolved = _resolve_addresses(hostname)
    if not resolved:
        # Cannot resolve – fail closed
        raise SSRFViolation(url, f"hostname '{hostname}' could not be resolved")

    if not _allow_private_targets():
        metadata_ips = {
            ipaddress.ip_address("169.254.169.254"),
            ipaddress.ip_address("169.254.170.2"),
        }
        for addr in resolved:
            if addr in metadata_ips:
                raise SSRFViolation(url, f"hostname '{hostname}' resolves to metadata endpoint {addr}")
            if _is_private_ip(addr):
                raise SSRFViolation(
                    url,
                    f"hostname '{hostname}' resolves to private/reserved address {addr}",
                )

    return url


def guard_url(url: str) -> str:
    """Convenience wrapper used by FastAPI dependencies.

    Raises :class:`SSRFViolation` on policy violation.
    Returns the validated URL unchanged.
    """
    return validate_url(url)
