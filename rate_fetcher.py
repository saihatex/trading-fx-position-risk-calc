from __future__ import annotations

import json
import urllib.request
from typing import Any

_RATES_CACHE: dict[str, Any] | None = None
_CACHE_SOURCE: str | None = None

PRIMARY_API_URL = "https://open.er-api.com/v6/latest/USD"
FALLBACK_API_URL = "https://api.frankfurter.app/latest?from=USD"


def _http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any] | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "risk-calculator/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                return json.loads(body)
    except Exception:
        return None
    return None


def fetch_usd_rates(timeout: float = 3.0, force_refresh: bool = False) -> tuple[dict[str, float] | None, str | None]:
    global _RATES_CACHE, _CACHE_SOURCE

    if _RATES_CACHE is not None and not force_refresh:
        return _RATES_CACHE, _CACHE_SOURCE

    data = _http_get_json(PRIMARY_API_URL, timeout=timeout)
    if data and data.get("result") == "success" and "rates" in data:
        rates = {str(k).upper(): float(v) for k, v in data["rates"].items()}
        _RATES_CACHE = rates
        _CACHE_SOURCE = "ExchangeRate-API (open.er-api.com)"
        return _RATES_CACHE, _CACHE_SOURCE

    data = _http_get_json(FALLBACK_API_URL, timeout=timeout)
    if data and "rates" in data:
        raw_rates = data["rates"]
        rates = {str(k).upper(): float(v) for k, v in raw_rates.items()}
        rates["USD"] = 1.0
        _RATES_CACHE = rates
        _CACHE_SOURCE = "Frankfurter API (frankfurter.app)"
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
    global _RATES_CACHE, _CACHE_SOURCE
    _RATES_CACHE = None
    _CACHE_SOURCE = None
