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


def test_jpy_pair_resolution_unified():
    profile = get_profile("ftmo")
    usdjpy = resolve_instrument(profile, "USDJPY", quote_rate=155.0)
    eurjpy = resolve_instrument(profile, "EURJPY", quote_rate=155.0)

    # 100,000 * 0.01 / 155.0 = 6.4516
    expected_pip_value = round(100_000 * 0.01 / 155.0, 4)
    assert usdjpy.pip_value_per_lot == expected_pip_value
    assert eurjpy.pip_value_per_lot == expected_pip_value


def test_effective_risk_lot_rounding():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    # Balance 1,540, 1% risk = $15.40
    # 25 pips SL -> raw lot = 15.40 / 250 = 0.0616 -> rounded lot = 0.06
    # Actual potential loss = 0.06 * 250 = $15.00
    # Effective risk % = 15.00 / 1540 = 0.974%
    result = calculate_position(
        trade=TradeInput(
            balance=1540,
            risk_pct=1.0,
            entry=1.0850,
            stop_loss=1.0825,
        ),
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )

    assert result.lot_size == 0.06
    assert result.potential_loss == 15.00
    assert result.effective_risk_pct == round((15.00 / 1540) * 100, 3)


def test_spread_inclusion():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    result = calculate_position(
        trade=TradeInput(
            balance=10_000,
            risk_pct=1.0,
            entry=1.0850,
            stop_loss=1.0830,  # 20 pips SL
            spread_pips=5.0,  # +5 pips spread = 25 pips total
        ),
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )

    assert result.sl_pips == 20.0
    assert result.spread_pips == 5.0
    assert result.effective_sl_pips == 25.0
    # 100 risk amount / (25 pips * 10) = 0.40 lots
    assert result.lot_size == 0.40
    assert result.spread_cost == round(0.40 * 5.0 * 10.0, 2)
    assert result.potential_loss == 100.0


def test_cli_parser_args():
    from cli import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--symbol", "EURJPY",
        "--balance", "10000",
        "--risk", "1",
        "--entry", "160.50",
        "--sl", "160.00",
        "--quote-rate", "155.0",
        "--spread", "2.0",
    ])

    assert args.symbol == "EURJPY"
    assert args.quote_rate == 155.0
    assert args.spread == 2.0


def test_risk_specified_in_cash_amount():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    # Risk specified in fixed dollar amount: $200 on $10,000 balance -> 2.0%
    result = calculate_position(
        trade=TradeInput(
            balance=10_000,
            risk_amount=200.0,
            entry=1.0850,
            stop_loss=1.0830,
        ),
        instrument=instrument,
        profile_name=profile.label,
        lot_rules=lot_rules,
    )

    assert result.risk_amount == 200.0
    assert result.risk_pct == 2.0
    assert result.lot_size == 1.0  # 200 / (20 * 10) = 1.0 lot


def test_risk_input_validation():
    profile = get_profile("ftmo")
    instrument = resolve_instrument(profile, "EURUSD")
    lot_rules = get_lot_rules()

    # Missing both risk_pct and risk_amount
    with pytest.raises(ValueError, match="Either risk percentage or risk cash amount must be provided"):
        calculate_position(
            trade=TradeInput(
                balance=10_000,
                entry=1.0850,
                stop_loss=1.0830,
            ),
            instrument=instrument,
            profile_name=profile.label,
            lot_rules=lot_rules,
        )

    # Invalid cash risk amount (exceeding balance)
    with pytest.raises(ValueError, match="Risk amount must be between 0 and balance"):
        calculate_position(
            trade=TradeInput(
                balance=10_000,
                risk_amount=15_000.0,
                entry=1.0850,
                stop_loss=1.0830,
            ),
            instrument=instrument,
            profile_name=profile.label,
            lot_rules=lot_rules,
        )


def test_universal_dynamic_conversion():
    profile = get_profile("ftmo")

    # 1. Indirect pair: USDCAD at 1.3500 -> 100,000 * 0.0001 / 1.35 = 7.4074
    usdcad = resolve_instrument(profile, "USDCAD", quote_rate=1.3500)
    assert usdcad.pip_value_per_lot == round(10.0 / 1.3500, 4)

    # 2. Cross pair multiplying: EURGBP with GBPUSD at 1.2700 -> 10.0 * 1.27 = 12.70
    eurgbp = resolve_instrument(profile, "EURGBP", quote_rate=1.2700)
    assert eurgbp.pip_value_per_lot == round(10.0 * 1.2700, 4)



