from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from config_loader import InstrumentSpec, LotRules


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class TradeInput:
    balance: float
    entry: float
    stop_loss: float
    risk_pct: float | None = None
    risk_amount: float | None = None
    take_profit: float | None = None
    spread_pips: float = 0.0


@dataclass(frozen=True)
class PositionResult:
    profile: str
    instrument: str
    direction: Direction
    balance: float
    risk_pct: float
    risk_amount: float
    effective_risk_pct: float
    entry: float
    stop_loss: float
    take_profit: float | None
    sl_pips: float
    spread_pips: float
    effective_sl_pips: float
    tp_pips: float | None
    rr_ratio: float | None
    pip_value_per_lot: float
    lot_size: float
    lot_size_raw: float
    potential_loss: float
    potential_profit: float | None
    position_value: float
    spread_cost: float
    rate_source: str | None = None


def detect_direction(entry: float, stop_loss: float) -> Direction:
    if stop_loss < entry:
        return Direction.LONG
    if stop_loss > entry:
        return Direction.SHORT
    raise ValueError("Stop loss must be different from entry price")


def validate_take_profit(direction: Direction, entry: float, take_profit: float) -> None:
    if direction == Direction.LONG and take_profit <= entry:
        raise ValueError("For a long, take profit must be above entry")
    if direction == Direction.SHORT and take_profit >= entry:
        raise ValueError("For a short, take profit must be below entry")


def price_distance_to_pips(price_distance: float, pip_size: float) -> float:
    if pip_size <= 0:
        raise ValueError("Pip size must be positive")
    return abs(price_distance) / pip_size


def round_lot(lot_size: float, rules: LotRules) -> float:
    if lot_size <= 0:
        return 0.0

    steps = round(lot_size / rules.step)
    rounded = steps * rules.step

    if rounded < rules.min:
        return 0.0
    if rounded > rules.max:
        return rules.max
    return round(rounded, 2)


def calculate_position(
    trade: TradeInput,
    instrument: InstrumentSpec,
    profile_name: str,
    lot_rules: LotRules,
) -> PositionResult:
    if trade.balance <= 0:
        raise ValueError("Balance must be positive")

    if trade.risk_pct is None and trade.risk_amount is None:
        raise ValueError("Either risk percentage or risk cash amount must be provided")

    if trade.risk_pct is not None:
        if not 0 < trade.risk_pct <= 100:
            raise ValueError("Risk percentage must be between 0 and 100")
        risk_pct = trade.risk_pct
        risk_amount = trade.balance * (risk_pct / 100)
    else:
        assert trade.risk_amount is not None
        if trade.risk_amount <= 0 or trade.risk_amount > trade.balance:
            raise ValueError(f"Risk amount must be between 0 and balance (${trade.balance:,.2f})")
        risk_amount = trade.risk_amount
        risk_pct = round((risk_amount / trade.balance) * 100, 3)

    if trade.spread_pips < 0:
        raise ValueError("Spread must be non-negative")

    direction = detect_direction(trade.entry, trade.stop_loss)
    sl_pips = price_distance_to_pips(trade.entry - trade.stop_loss, instrument.pip_size)

    if sl_pips <= 0:
        raise ValueError("Stop loss distance must be greater than zero")

    effective_sl_pips = sl_pips + trade.spread_pips

    tp_pips: float | None = None
    rr_ratio: float | None = None
    potential_profit: float | None = None

    if trade.take_profit is not None:
        validate_take_profit(direction, trade.entry, trade.take_profit)
        tp_pips = price_distance_to_pips(trade.take_profit - trade.entry, instrument.pip_size)
        rr_ratio = round(tp_pips / sl_pips, 2)

    lot_size_raw = risk_amount / (effective_sl_pips * instrument.pip_value_per_lot)
    lot_size = round_lot(lot_size_raw, lot_rules)

    potential_loss = round(lot_size * effective_sl_pips * instrument.pip_value_per_lot, 2)
    spread_cost = round(lot_size * trade.spread_pips * instrument.pip_value_per_lot, 2)
    effective_risk_pct = round((potential_loss / trade.balance) * 100, 3)

    if tp_pips is not None:
        potential_profit = round(lot_size * tp_pips * instrument.pip_value_per_lot, 2)

    position_value = round(lot_size * instrument.contract_size, 2)

    return PositionResult(
        profile=profile_name,
        instrument=instrument.symbol,
        direction=direction,
        balance=trade.balance,
        risk_pct=risk_pct,
        risk_amount=round(risk_amount, 2),
        effective_risk_pct=effective_risk_pct,
        entry=trade.entry,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        sl_pips=round(sl_pips, 1),
        spread_pips=round(trade.spread_pips, 1),
        effective_sl_pips=round(effective_sl_pips, 1),
        tp_pips=round(tp_pips, 1) if tp_pips is not None else None,
        rr_ratio=rr_ratio,
        pip_value_per_lot=instrument.pip_value_per_lot,
        lot_size=lot_size,
        lot_size_raw=round(lot_size_raw, 4),
        potential_loss=potential_loss,
        potential_profit=potential_profit,
        position_value=position_value,
        spread_cost=spread_cost,
        rate_source=instrument.rate_source,
    )


def format_result(result: PositionResult) -> str:
    lines = [
        f"Profile:          {result.profile}",
        f"Instrument:       {result.instrument}",
        f"Direction:        {result.direction.value.upper()}",
        "",
        f"Balance:          ${result.balance:,.2f}",
        f"Risk (requested): {result.risk_pct}% (${result.risk_amount:,.2f})",
        f"Effective risk:   {result.effective_risk_pct:.2f}% (${result.potential_loss:,.2f})",
        "",
        f"Entry:            {result.entry}",
    ]

    if result.spread_pips > 0:
        lines.append(
            f"Stop Loss:        {result.stop_loss}  ({result.sl_pips} pips + {result.spread_pips} spread = {result.effective_sl_pips} pips total)"
        )
    else:
        lines.append(f"Stop Loss:        {result.stop_loss}  ({result.sl_pips} pips)")

    if result.take_profit is not None:
        lines.append(f"Take Profit:      {result.take_profit}  ({result.tp_pips} pips)")
        lines.append(f"R:R:              1:{result.rr_ratio}")

    pip_val_str = f"Pip value / lot:  ${result.pip_value_per_lot:.4f}"
    if result.rate_source:
        pip_val_str += f"  [{result.rate_source}]"

    lines.extend(
        [
            "",
            pip_val_str,
            f"Lot size:         {result.lot_size:.2f}",
            f"Position value:   ${result.position_value:,.2f}",
        ]
    )

    if result.spread_pips > 0:
        lines.append(f"Spread cost:      ${result.spread_cost:,.2f}")

    lines.append(f"Potential loss:   ${result.potential_loss:,.2f}")

    if result.potential_profit is not None:
        lines.append(f"Potential profit: ${result.potential_profit:,.2f}")

    if result.lot_size == 0:
        lines.append("")
        lines.append("Warning: calculated lot is below minimum lot size.")

    return "\n".join(lines)
