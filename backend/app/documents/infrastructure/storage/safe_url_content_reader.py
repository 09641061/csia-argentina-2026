from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import certifi

from app.documents.infrastructure.storage.exceptions import DocumentStorageReadError

_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "instance-data",
}
_CLOUD_METADATA_ADDRESSES = {"169.254.169.254", "100.100.100.200", "fd00:ec2::254"}


class SafeUrlContentReader:
    """
    Fetches a stored document over HTTPS with SSRF protections.

    Only the exact hosts the configured storage backend is allowed to use can be
    reached; every resolved address is checked so a DNS record pointing at
    loopback, a private range or a cloud metadata endpoint is rejected.
    Redirects are refused outright rather than re-validated.
    """

    def __init__(self, allowed_hosts: frozenset[str], max_content_bytes: int, timeout_seconds: int = 30) -> None:
        if not allowed_hosts:
            raise ValueError("At least one allowed host is required")
        if max_content_bytes <= 0 or timeout_seconds <= 0:
            raise ValueError("Size and timeout limits must be positive")
        self._allowed_hosts = frozenset(host.lower() for host in allowed_hosts)
        self._max_content_bytes = max_content_bytes
        self._timeout_seconds = timeout_seconds

    async def read(self, url: str) -> bytes:
        return await asyncio.to_thread(self._read, url)

    def _read(self, url: str) -> bytes:
        self._assert_url_is_allowed(url)
        context = ssl.create_default_context(cafile=certifi.where())
        request = Request(url, method="GET", headers={"Accept": "application/octet-stream"})
        try:
            with urlopen(request, context=context, timeout=self._timeout_seconds) as response:
                if response.geturl() != url:
                    raise DocumentStorageReadError("Redirected document references are rejected")
                content = response.read(self._max_content_bytes + 1)
        except DocumentStorageReadError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise DocumentStorageReadError("The stored document could not be downloaded") from error

        if len(content) > self._max_content_bytes:
            raise DocumentStorageReadError("The stored document exceeds the analysis size limit")
        if not content:
            raise DocumentStorageReadError("The stored document is empty")
        return content

    def _assert_url_is_allowed(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise DocumentStorageReadError("Only HTTPS document references are accepted")
        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname in _BLOCKED_HOSTNAMES:
            raise DocumentStorageReadError("Rejected document reference host")
        if hostname not in self._allowed_hosts:
            raise DocumentStorageReadError("Document reference host is not allowed")
        for address in self._resolve_addresses(hostname):
            if address in _CLOUD_METADATA_ADDRESSES:
                raise DocumentStorageReadError("Rejected document reference host")
            parsed_address = ipaddress.ip_address(address)
            if (
                parsed_address.is_private
                or parsed_address.is_loopback
                or parsed_address.is_link_local
                or parsed_address.is_reserved
                or parsed_address.is_multicast
                or parsed_address.is_unspecified
            ):
                raise DocumentStorageReadError("Document reference resolves to an internal address")

    def _resolve_addresses(self, hostname: str) -> list[str]:
        try:
            infos = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror as error:
            raise DocumentStorageReadError("Document reference host could not be resolved") from error
        return [info[4][0] for info in infos]
