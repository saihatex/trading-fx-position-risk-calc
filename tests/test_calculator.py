import pytest

from calculator import Direction, TradeInput, calculate_position
from config_loader import get_lot_rules, get_profile, resolve_instrument


def test_long_position_from_prices():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    result = calculate_position(
        trade=TradeInput(
            balance=10_000,
            risk_pct=1.0,
            entry=1.0850,
            stop_loss=1.0830,
            take_profit=1.0890,
        ),
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )

    assert result.direction == Direction.LONG
    assert result.sl_pips == 20.0
    assert result.tp_pips == 40.0
    assert result.rr_ratio == 2.0
    assert result.lot_size == 0.5
    assert result.potential_loss == 100.0
    assert result.potential_profit == 200.0


def test_short_position_from_prices():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    result = calculate_position(
        trade=TradeInput(
            balance=10_000,
            risk_pct=1.0,
            entry=1.0850,
            stop_loss=1.0870,
            take_profit=1.0810,
        ),
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )

    assert result.direction == Direction.SHORT
    assert result.sl_pips == 20.0
    assert result.tp_pips == 40.0
    assert result.rr_ratio == 2.0


def test_invalid_take_profit_for_long():
    with pytest.raises(ValueError, match="take profit must be above entry"):
        calculate_position(
            trade=TradeInput(
                balance=10_000,
                risk_pct=1.0,
                entry=1.0850,
                stop_loss=1.0830,
                take_profit=1.0840,
            ),
            instrument=resolve_instrument(get_profile("ftmo"), "EURUSD"),
            profile_name="FTMO",
            lot_rules=get_lot_rules(),
        )


def test_profile_specific_instrument():
    profile = get_profile("ftmo")
    xau = resolve_instrument(profile, "XAUUSD")

    assert xau.pip_size == 0.01
    assert xau.contract_size == 100
