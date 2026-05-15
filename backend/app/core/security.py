import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import Header, HTTPException, status

from app.core.config import settings

PRIVATE_HOSTS = {"localhost", "localhost.localdomain"}


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


def validate_public_http_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL hostname is required")
    hostname = parsed.hostname.lower()
    if hostname in PRIVATE_HOSTS:
        raise ValueError("Private/internal hostnames are blocked")

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError("Hostname could not be resolved") from exc

    for item in addresses:
        ip_text = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Private/internal IP ranges are blocked for scanner safety")

    return raw_url.strip()
