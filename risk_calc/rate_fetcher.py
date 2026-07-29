from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

CACHE_TTL_SECONDS = 300

_RATES_CACHE: dict[str, float] | None = None
_CACHE_SOURCE: str | None = None
_CACHE_TIMESTAMP: float = 0.0

PRIMARY_API_URL = "https://open.er-api.com/v6/latest/USD"
FALLBACK_API_URL = "https://api.frankfurter.app/latest?from=USD"


def _http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any] | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "risk-calculator/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                return json.loads(body)
    except Exception:
        return None
    return None


def _cache_is_valid() -> bool:
    return _RATES_CACHE is not None and (time.monotonic() - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS


def fetch_usd_rates(timeout: float = 3.0, force_refresh: bool = False) -> tuple[dict[str, float] | None, str | None]:
    global _RATES_CACHE, _CACHE_SOURCE, _CACHE_TIMESTAMP

    if not force_refresh and _cache_is_valid():
        return _RATES_CACHE, _CACHE_SOURCE

    data = _http_get_json(PRIMARY_API_URL, timeout=timeout)
    if data and data.get("result") == "success" and "rates" in data:
        _RATES_CACHE = {str(k).upper(): float(v) for k, v in data["rates"].items()}
        _CACHE_SOURCE = "ExchangeRate-API (open.er-api.com)"
        _CACHE_TIMESTAMP = time.monotonic()
        return _RATES_CACHE, _CACHE_SOURCE

    data = _http_get_json(FALLBACK_API_URL, timeout=timeout)
    if data and "rates" in data:
        _RATES_CACHE = {str(k).upper(): float(v) for k, v in data["rates"].items()}
        _RATES_CACHE["USD"] = 1.0
        _CACHE_SOURCE = "Frankfurter API (frankfurter.app)"
        _CACHE_TIMESTAMP = time.monotonic()
        return _RATES_CACHE, _CACHE_SOURCE

    return None, None


def get_conversion_rate(
    conversion_pair: str,
    timeout: float = 3.0,
    force_refresh: bool = False,
) -> tuple[float | None, str | None]:
    conversion_pair = conversion_pair.upper()
    rates, source = fetch_usd_rates(timeout=timeout, force_refresh=force_refresh)
    if not rates or not source:
        return None, None

    if conversion_pair.startswith("USD"):
        quote = conversion_pair[3:]
        if quote in rates:
            return rates[quote], source

    elif conversion_pair.endswith("USD"):
        base = conversion_pair[:3]
        if base in rates and rates[base] > 0:
            return round(1.0 / rates[base], 6), source

    return None, None


def clear_cache() -> None:
    global _RATES_CACHE, _CACHE_SOURCE, _CACHE_TIMESTAMP
    _RATES_CACHE = None
    _CACHE_SOURCE = None
    _CACHE_TIMESTAMP = 0.0
