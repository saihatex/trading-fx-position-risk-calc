from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    pip_size: float
    contract_size: float
    pip_value_per_lot: float


@dataclass(frozen=True)
class LotRules:
    min: float
    step: float
    max: float


@dataclass(frozen=True)
class Profile:
    name: str
    label: str
    account_currency: str
    instruments: dict[str, InstrumentSpec]


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or CONFIG_PATH
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_lot_rules(config: dict[str, Any] | None = None) -> LotRules:
    config = config or load_config()
    lot = config.get("lot", {})
    return LotRules(
        min=float(lot.get("min", 0.01)),
        step=float(lot.get("step", 0.01)),
        max=float(lot.get("max", 100.0)),
    )


def get_profile(name: str | None = None, config: dict[str, Any] | None = None) -> Profile:
    config = config or load_config()
    profile_name = name or config.get("default_profile", "ftmo")
    raw_profiles = config["profiles"]

    if profile_name not in raw_profiles:
        available = ", ".join(sorted(raw_profiles))
        raise KeyError(f"Unknown profile '{profile_name}'. Available: {available}")

    raw = raw_profiles[profile_name]
    instruments = {
        symbol: InstrumentSpec(
            symbol=symbol,
            pip_size=float(spec["pip_size"]),
            contract_size=float(spec["contract_size"]),
            pip_value_per_lot=float(spec["pip_value_per_lot"]),
        )
        for symbol, spec in raw["instruments"].items()
    }

    return Profile(
        name=profile_name,
        label=str(raw.get("label", profile_name)),
        account_currency=str(raw.get("account_currency", "USD")),
        instruments=instruments,
    )


def resolve_instrument(
    profile: Profile,
    symbol: str,
    quote_rate: float | None = None,
) -> InstrumentSpec:
    symbol = symbol.upper()
    if symbol not in profile.instruments:
        available = ", ".join(sorted(profile.instruments))
        raise KeyError(f"Instrument '{symbol}' not configured for {profile.label}. Available: {available}")

    spec = profile.instruments[symbol]

    # Dynamic pip value for JPY-quoted pairs when quote_rate is supplied.
    if quote_rate and symbol.endswith("JPY") and not symbol.startswith("USD"):
        pip_value = spec.contract_size * spec.pip_size / quote_rate
        return InstrumentSpec(
            symbol=spec.symbol,
            pip_size=spec.pip_size,
            contract_size=spec.contract_size,
            pip_value_per_lot=round(pip_value, 4),
        )

    if quote_rate and symbol == "USDJPY":
        pip_value = spec.contract_size * spec.pip_size / quote_rate
        return InstrumentSpec(
            symbol=spec.symbol,
            pip_size=spec.pip_size,
            contract_size=spec.contract_size,
            pip_value_per_lot=round(pip_value, 4),
        )

    return spec


def list_profiles(config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_config()
    return sorted(config["profiles"].keys())
