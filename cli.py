from __future__ import annotations

import argparse
import sys

from calculator import TradeInput, calculate_position, format_result
from config_loader import get_lot_rules, get_profile, list_profiles, resolve_instrument


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Position size calculator for forex and metals trading.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help=f"Broker/prop profile from config.yaml (default: from config). Available: {', '.join(list_profiles())}",
    )
    parser.add_argument("--symbol", required=False, help="Instrument symbol, e.g. EURUSD, XAUUSD")
    parser.add_argument("--balance", type=float, help="Account balance")
    parser.add_argument("--risk", type=float, help="Risk per trade in percent, e.g. 1.0")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--sl", type=float, help="Stop loss price")
    parser.add_argument("--tp", type=float, help="Take profit price")
    parser.add_argument(
        "--quote-rate",
        type=float,
        help="Current quote rate for dynamic pip value (useful for USDJPY)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive mode",
    )
    return parser


def prompt_float(label: str) -> float:
    while True:
        raw = input(f"{label}: ").strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print("Enter a valid number.")


def prompt_optional_float(label: str) -> float | None:
    raw = input(f"{label} (optional): ").strip().replace(",", ".")
    if not raw:
        return None
    return float(raw)


def run_interactive() -> None:
    profiles = list_profiles()
    print("Available profiles:", ", ".join(profiles))
    profile_name = input("Profile: ").strip().lower() or None

    profile = get_profile(profile_name)
    print(f"Using profile: {profile.label}")

    print("Available symbols:", ", ".join(sorted(profile.instruments)))
    symbol = input("Symbol: ").strip().upper()

    quote_rate = None
    if symbol.endswith("JPY"):
        quote_rate = prompt_optional_float("Quote rate for pip value")

    balance = prompt_float("Account balance")
    risk = prompt_float("Risk %")
    entry = prompt_float("Entry price")
    sl = prompt_float("Stop loss price")
    tp = prompt_optional_float("Take profit price")

    _run_calculation(profile.name, symbol, balance, risk, entry, sl, tp, quote_rate)


def _run_calculation(
    profile_name: str | None,
    symbol: str,
    balance: float,
    risk: float,
    entry: float,
    sl: float,
    tp: float | None,
    quote_rate: float | None,
) -> None:
    profile = get_profile(profile_name)
    instrument = resolve_instrument(profile, symbol, quote_rate=quote_rate)
    lot_rules = get_lot_rules()

    trade = TradeInput(
        balance=balance,
        risk_pct=risk,
        entry=entry,
        stop_loss=sl,
        take_profit=tp,
    )

    result = calculate_position(
        trade=trade,
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )
    print()
    print(format_result(result))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.interactive or not all([args.symbol, args.balance, args.risk, args.entry, args.sl]):
        run_interactive()
        return 0

    _run_calculation(
        profile_name=args.profile,
        symbol=args.symbol,
        balance=args.balance,
        risk=args.risk,
        entry=args.entry,
        sl=args.sl,
        tp=args.tp,
        quote_rate=args.quote_rate,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
