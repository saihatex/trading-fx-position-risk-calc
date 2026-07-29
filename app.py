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

            direction_class = "direction-long" if result.direction.value == "long" else "direction-short"
            direction_label = "▲ LONG" if result.direction.value == "long" else "▼ SHORT"

            tp_row = ""
            if result.tp_pips is not None:
                tp_row = f"""
                <div class="result-row">
                    <span class="result-label">Take Profit</span>
                    <span class="result-value">{result.take_profit} &nbsp;({result.tp_pips} pips)</span>
                </div>
                <div class="result-row">
                    <span class="result-label">R:R Ratio</span>
                    <span class="result-value">1:{result.rr_ratio}</span>
                </div>"""

            spread_row = ""
            if result.spread_pips > 0:
                spread_row = f"""
                <div class="result-row">
                    <span class="result-label">Spread cost</span>
                    <span class="result-value">${result.spread_cost:,.2f}</span>
                </div>"""

            sl_pips_label = f"{result.sl_pips} pips"
            if result.spread_pips > 0:
                sl_pips_label = f"{result.sl_pips} + {result.spread_pips} spread = {result.effective_sl_pips} pips"

            source_note = ""
            if result.rate_source:
                source_note = f'<div class="source-note">Rate source: {result.rate_source}</div>'

            lot_warn = ""
            if result.lot_size == 0:
                lot_warn = '<div style="color:#f87171;margin-top:0.6rem;font-size:0.8rem;">⚠ Lot size below minimum — reduce SL or increase balance/risk.</div>'

            st.markdown(f"""
            <div class="result-box">
                <div class="result-row">
                    <span class="result-label">Direction</span>
                    <span class="result-value {direction_class}">{direction_label}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Stop Loss</span>
                    <span class="result-value">{result.stop_loss} &nbsp;({sl_pips_label})</span>
                </div>
                {tp_row}
                <div style="border-top:1px solid #2d2d2d;margin:0.7rem 0;"></div>
                <div class="result-row">
                    <span class="result-label">Risk requested</span>
                    <span class="result-value">{result.risk_pct}% &nbsp;(${result.risk_amount:,.2f})</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Effective risk</span>
                    <span class="result-value">{result.effective_risk_pct:.2f}% &nbsp;(${result.potential_loss:,.2f})</span>
                </div>
                {spread_row}
                <div style="border-top:1px solid #2d2d2d;margin:0.7rem 0;"></div>
                <div class="result-row">
                    <span class="result-label">Pip value / lot</span>
                    <span class="result-value">${result.pip_value_per_lot:.4f}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Lot size</span>
                    <span class="result-value highlight">{result.lot_size:.2f}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Position value</span>
                    <span class="result-value">${result.position_value:,.2f}</span>
                </div>
                {lot_warn}
                {source_note}
            </div>
            """, unsafe_allow_html=True)

        except ValueError as e:
            st.error(str(e))
        except KeyError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("")
st.caption("Rates via [ExchangeRate-API](https://open.er-api.com) · [GitHub](https://github.com/saihatex/trading-fx-position-risk-calc)")
