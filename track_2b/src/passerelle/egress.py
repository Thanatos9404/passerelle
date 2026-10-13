"""Egress guard: the only outbound destination allowed is the configured LLM endpoint.

Two layers:
1. ``check_url`` — every HTTP request made by Passerelle's LLM client is checked by host.
2. ``install_socket_guard`` — a process-wide patch of ``socket.socket.connect`` refuses TCP/UDP
   connections to any non-loopback address that does not belong to an allowed host, so a
   third-party library cannot phone home either (defence in depth; in the air-gapped
   deployment the container network is additionally ``internal``).

Blocked attempts raise :class:`EgressBlocked` and are written to the audit log.
"""

from __future__ import annotations

import ipaddress
import socket
import threading
from urllib.parse import urlparse

_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "ip6-localhost"}
_lock = threading.RLock()
_allowed_hosts: set[str] = set()
_allowed_ips: set[str] = set()
_blocked_count = 0
_installed = False
_orig_connect = socket.socket.connect
_orig_connect_ex = socket.socket.connect_ex


class EgressBlocked(ConnectionRefusedError):
    """Raised when code tries to reach a destination outside the allowlist."""


def configure(llm_base_url: str, extra_hosts: tuple[str, ...] = ()) -> None:
    host = (urlparse(llm_base_url).hostname or "").lower()
    with _lock:
        _allowed_hosts.clear()
        _allowed_hosts.update(h for h in {host, *extra_hosts} if h)
        _allowed_ips.clear()
        _refresh_ips()


def _refresh_ips() -> None:
    for h in list(_allowed_hosts):
        try:
            for info in socket.getaddrinfo(h, None):
                _allowed_ips.add(info[4][0])
        except OSError:
            pass


def allowed_hosts() -> list[str]:
    return sorted(_allowed_hosts)


def _is_loopback(host: str) -> bool:
    if host.lower() in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False


def is_allowed_host(host: str | None) -> bool:
    if not host:
        return False
    host = host.lower().strip("[]")
    return _is_loopback(host) or host in _allowed_hosts or host in _allowed_ips


def _note_block(target: str) -> None:
    global _blocked_count
    with _lock:
        _blocked_count += 1
    try:  # never let auditing break the guard
        from .audit import get_audit_log

        get_audit_log().record("egress_blocked", meta={"target_hash_only": True}, inputs={"target": target})
    except Exception:  # pragma: no cover
        pass


def check_url(url: str) -> None:
    host = urlparse(url).hostname
    if not is_allowed_host(host):
        _note_block(url)
        raise EgressBlocked(f"egress to {host!r} blocked (allowed: {allowed_hosts()})")


def _check_address(address) -> None:
    if not isinstance(address, tuple) or not address:
        return  # AF_UNIX or unusual address families
    host = str(address[0])
    if is_allowed_host(host):
        return
    with _lock:
        _refresh_ips()  # DNS of an allowed host may have changed
    if is_allowed_host(host):
        return
    _note_block(f"{host}:{address[1] if len(address) > 1 else ''}")
    raise EgressBlocked(f"egress to {host} blocked by Passerelle egress guard")


def _guarded_connect(self, address):
    _check_address(address)
    return _orig_connect(self, address)


def _guarded_connect_ex(self, address):
    _check_address(address)
    return _orig_connect_ex(self, address)


def install_socket_guard() -> None:
    global _installed
    with _lock:
        if _installed:
            return
        socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
        _installed = True


def uninstall_socket_guard() -> None:
    global _installed
    with _lock:
        socket.socket.connect = _orig_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = _orig_connect_ex  # type: ignore[method-assign]
        _installed = False


def status() -> dict:
    return {
        "allowed_hosts": allowed_hosts(),
        "socket_guard": _installed,
        "blocked_attempts": _blocked_count,
    }
