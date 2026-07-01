# services/proxy.py
"""
Per-client proxy configuration for the Telegram traffic only.

Telegram is unreachable without a proxy in some regions, while the LLM
endpoint and Postgres must stay direct. Rather than proxying the whole
process at the OS/network level, each Telegram client reads the proxy from
here and routes through it; everything else connects directly.

Set `TELEGRAM_PROXY_URL` in .env (e.g. a v2ray/xray local SOCKS inbound):
    TELEGRAM_PROXY_URL=socks5://127.0.0.1:10808
Leave it unset to connect directly (e.g. when running outside the country).
"""

from typing import Optional, Tuple
from urllib.parse import urlparse

import socks

from config import settings


def get_proxy_url() -> Optional[str]:
    """Proxy URL string for httpx-based clients (python-telegram-bot), or None."""
    url = settings.telegram_proxy_url
    return url or None


# urlparse scheme -> PySocks proxy type (used by Telethon)
_SCHEME_TO_SOCKS_TYPE = {
    "socks5": socks.SOCKS5,
    "socks5h": socks.SOCKS5,   # 'h' = resolve DNS on the proxy side
    "socks4": socks.SOCKS4,
    "socks4a": socks.SOCKS4,
    "http": socks.HTTP,
    "https": socks.HTTP,
}


def get_telethon_proxy() -> Optional[Tuple]:
    """
    Parse the proxy URL into the PySocks tuple Telethon expects, or None.

    Format: (proxy_type, host, port, rdns[, username, password])
    rdns=True routes DNS through the proxy, which is what we want in a
    censored network.
    """
    url = get_proxy_url()
    if not url:
        return None

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    proxy_type = _SCHEME_TO_SOCKS_TYPE.get(scheme)
    if proxy_type is None:
        raise ValueError(
            f"Unsupported TELEGRAM_PROXY_URL scheme '{scheme}'. "
            f"Use one of: {', '.join(sorted(_SCHEME_TO_SOCKS_TYPE))}."
        )
    if not parsed.hostname or not parsed.port:
        raise ValueError(
            "TELEGRAM_PROXY_URL must include host and port, "
            "e.g. socks5://127.0.0.1:10808"
        )

    if parsed.username:
        return (proxy_type, parsed.hostname, parsed.port, True,
                parsed.username, parsed.password)
    return (proxy_type, parsed.hostname, parsed.port, True)
