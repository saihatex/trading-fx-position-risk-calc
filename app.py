from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from calculator import TradeInput, calculate_position
from config_loader import get_lot_rules, get_profile, list_profiles, resolve_instrument

st.set_page_config(
    page_title="Risk Calculator",
    page_icon="📐",
    layout="centered",
)

st.markdown("""
<style>
    .block-container { max-width: 680px; padding-top: 2rem; }
    .result-box {
        background: #0e1117;
        border: 1px solid #2d2d2d;
        border-radius: 10px;
        padding: 1.4rem 1.6rem;
        margin-top: 1rem;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.88rem;
        line-height: 1.9;
    }
    .result-row { display: flex; justify-content: space-between; }
    .result-label { color: #888; }
    .result-value { color: #f0f0f0; font-weight: 500; }
    .result-value.highlight { color: #4ade80; font-size: 1.05rem; }
    .result-value.warn { color: #facc15; }
    .result-value.direction-long { color: #4ade80; }
    .result-value.direction-short { color: #f87171; }
    .source-note { color: #555; font-size: 0.75rem; margin-top: 0.6rem; }
    .stSelectbox label, .stNumberInput label, .stToggle label { font-size: 0.85rem !important; color: #aaa !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.4rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📐 Risk Calculator")
st.caption("Position sizing for forex and metals. Live rates fetched automatically.")

st.divider()

profiles = list_profiles()
profile_labels = {p: get_profile(p).label for p in profiles}

col1, col2 = st.columns([1, 1])

with col1:
    selected_profile_key = st.selectbox(
        "Broker / Profile",
        options=profiles,
        format_func=lambda k: profile_labels[k],
    )

profile = get_profile(selected_profile_key)
symbols = sorted(profile.instruments.keys())

with col2:
    symbol = st.selectbox("Instrument", options=symbols)

st.markdown("")

col3, col4 = st.columns([1, 1])

with col3:
    balance = st.number_input("Account Balance ($)", min_value=1.0, value=10000.0, step=500.0)

with col4:
    risk_mode = st.radio("Risk mode", ["Percent %", "Fixed $"], horizontal=True, label_visibility="collapsed")

col5, col6 = st.columns([1, 1])

with col5:
    if risk_mode == "Percent %":
        risk_pct = st.number_input("Risk (%)", min_value=0.01, max_value=100.0, value=1.0, step=0.1)
        risk_amount = None
    else:
        risk_amount = st.number_input("Risk ($)", min_value=1.0, value=100.0, step=10.0)
        risk_pct = None

with col6:
    spread = st.number_input("Spread (pips)", min_value=0.0, value=0.0, step=0.5)

col7, col8, col9 = st.columns(3)

with col7:
    entry = st.number_input("Entry Price", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="e.g. 1.08500")

with col8:
    sl = st.number_input("Stop Loss", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="e.g. 1.08300")

with col9:
    tp = st.number_input("Take Profit (opt.)", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="optional")

no_live_rate = st.toggle("Offline mode (use static rates)", value=False)

st.markdown("")
calculate = st.button("Calculate", type="primary", use_container_width=True)

if calculate:
    errors = []
    if not entry:
        errors.append("Enter a valid Entry price.")
    if not sl:
        errors.append("Enter a valid Stop Loss.")
    if entry and sl and entry == sl:
        errors.append("Entry and Stop Loss cannot be equal.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        try:
            instrument = resolve_instrument(
                profile,
                symbol,
                auto_fetch_rate=not no_live_rate,
            )
            lot_rules = get_lot_rules()
            trade = TradeInput(
                balance=balance,
                risk_pct=risk_pct,
                risk_amount=risk_amount,
                entry=entry,
                stop_loss=sl,
                take_profit=tp,
                spread_pips=spread,
            )
            result = calculate_position(
                trade=trade,
                instrument=instrument,
                profile_name=profile.label,
                lot_rules=lot_rules,
            )

            st.divider()

            direction_color = "normal" if result.direction.value == "long" else "inverse"
            direction_label = "▲ LONG" if result.direction.value == "long" else "▼ SHORT"

            c1, c2, c3 = st.columns(3)
            c1.metric("Direction", direction_label)
            c2.metric("Lot size", f"{result.lot_size:.2f}")
            if result.rr_ratio is not None:
                c3.metric("R:R", f"1:{result.rr_ratio}")
            else:
                c3.metric("Effective risk", f"{result.effective_risk_pct:.2f}%")

            st.markdown("")

            sl_pips_label = f"{result.sl_pips} pips"
            if result.spread_pips > 0:
                sl_pips_label = f"{result.sl_pips} + {result.spread_pips} spread = {result.effective_sl_pips} pips"

            rows = [
                ("Stop Loss", f"{result.stop_loss}  ({sl_pips_label})"),
            ]
            if result.tp_pips is not None:
                rows.append(("Take Profit", f"{result.take_profit}  ({result.tp_pips} pips)"))
                rows.append(("R:R Ratio", f"1:{result.rr_ratio}"))

            rows += [
                ("───", "───"),
                ("Risk requested", f"{result.risk_pct}%  (${result.risk_amount:,.2f})"),
                ("Effective risk", f"{result.effective_risk_pct:.2f}%  (${result.potential_loss:,.2f})"),
            ]
            if result.spread_pips > 0:
                rows.append(("Spread cost", f"${result.spread_cost:,.2f}"))

            rows += [
                ("───", "───"),
                ("Pip value / lot", f"${result.pip_value_per_lot:.4f}"),
                ("Lot size", f"{result.lot_size:.2f}"),
                ("Position value", f"${result.position_value:,.2f}"),
            ]
            if result.potential_profit is not None:
                rows.append(("Potential profit", f"${result.potential_profit:,.2f}"))

            for label, value in rows:
                if label == "───":
                    st.markdown("<hr style='margin:4px 0;border-color:#2d2d2d'>", unsafe_allow_html=True)
                    continue
                ra, rb = st.columns([1, 1])
                ra.markdown(f"<span style='color:#888;font-size:0.85rem'>{label}</span>", unsafe_allow_html=True)
                rb.markdown(f"<span style='font-size:0.85rem'>{value}</span>", unsafe_allow_html=True)

            if result.lot_size == 0:
                st.warning("Lot size is below minimum — reduce SL distance or increase balance/risk.")

            if result.rate_source:
                st.caption(f"Rate: {result.rate_source}")

        except ValueError as e:
            st.error(str(e))
        except KeyError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("")
st.caption("Rates via [ExchangeRate-API](https://open.er-api.com) · [GitHub](https://github.com/saihatex/trading-fx-position-risk-calc)")

