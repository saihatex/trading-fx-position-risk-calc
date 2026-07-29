from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from calculator import TradeInput, calculate_position
from config_loader import get_lot_rules, get_profile, list_profiles, resolve_instrument

st.set_page_config(page_title="Risk Calculator", page_icon=None, layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 600px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

h1 { font-size: 1.1rem !important; font-weight: 500 !important; letter-spacing: 0.08em; color: #fff !important; }

.stSelectbox label, .stNumberInput label, .stRadio label,
.stToggle label, [data-testid="stWidgetLabel"] {
    font-size: 0.75rem !important;
    color: #555 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.stButton > button {
    background: #fff !important;
    color: #000 !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em;
    padding: 0.55rem 1.2rem !important;
}

.stButton > button:hover {
    background: #e5e5e5 !important;
}

.result-block {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    margin-top: 2rem;
    border-top: 1px solid #222;
    padding-top: 1.4rem;
}

.result-row {
    display: flex;
    justify-content: space-between;
    padding: 0.18rem 0;
    color: #aaa;
}

.result-row .val { color: #fff; }
.result-row .val.long { color: #22c55e; }
.result-row .val.short { color: #ef4444; }

.lot-block {
    font-family: 'JetBrains Mono', monospace;
    margin: 1.4rem 0 0.8rem 0;
    padding: 1rem 1.2rem;
    background: #111;
    border: 1px solid #1f1f1f;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.lot-label { font-size: 0.75rem; color: #555; text-transform: uppercase; letter-spacing: 0.06em; }
.lot-value { font-size: 2rem; font-weight: 600; color: #fff; letter-spacing: -0.02em; }

.sep { border: none; border-top: 1px solid #1e1e1e; margin: 0.8rem 0; }

.source-line { font-size: 0.72rem; color: #333; margin-top: 1rem; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>RISK CALCULATOR</h1>", unsafe_allow_html=True)
st.markdown("<div style='color:#444;font-size:0.78rem;margin-bottom:2rem'>Forex & metals position sizing. Live rates applied automatically.</div>", unsafe_allow_html=True)

profiles = list_profiles()
profile_labels = {p: get_profile(p).label for p in profiles}

col1, col2 = st.columns(2)
with col1:
    selected_profile_key = st.selectbox("Profile", options=profiles, format_func=lambda k: profile_labels[k])

profile = get_profile(selected_profile_key)
symbols = sorted(profile.instruments.keys())

with col2:
    symbol = st.selectbox("Instrument", options=symbols)

col3, col4 = st.columns(2)
with col3:
    balance = st.number_input("Balance ($)", min_value=1.0, value=10000.0, step=500.0)
with col4:
    risk_mode = st.radio("Risk mode", ["% of balance", "Fixed $"], horizontal=True)

col5, col6 = st.columns(2)
with col5:
    if risk_mode == "% of balance":
        risk_pct = st.number_input("Risk (%)", min_value=0.01, max_value=100.0, value=1.0, step=0.1)
        risk_amount = None
    else:
        risk_amount = st.number_input("Risk ($)", min_value=1.0, value=100.0, step=10.0)
        risk_pct = None
with col6:
    spread = st.number_input("Spread (pips)", min_value=0.0, value=0.0, step=0.5)

col7, col8, col9 = st.columns(3)
with col7:
    entry = st.number_input("Entry", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="0.00000")
with col8:
    sl = st.number_input("Stop Loss", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="0.00000")
with col9:
    tp = st.number_input("Take Profit", min_value=0.0001, value=None, step=0.0001, format="%.5f", placeholder="optional")

offline = st.toggle("Offline (static rates)", value=False)

st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)
go = st.button("Calculate", use_container_width=True)

if go:
    errors = []
    if not entry:
        errors.append("Entry price is required.")
    if not sl:
        errors.append("Stop loss is required.")
    if entry and sl and entry == sl:
        errors.append("Entry and stop loss must differ.")

    if errors:
        for e in errors:
            st.error(e, icon=None)
    else:
        try:
            instrument = resolve_instrument(profile, symbol, auto_fetch_rate=not offline)
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

            is_long = result.direction.value == "long"
            dir_class = "long" if is_long else "short"
            dir_label = "LONG" if is_long else "SHORT"

            sl_label = f"{result.sl_pips} pips"
            if result.spread_pips > 0:
                sl_label = f"{result.sl_pips} + {result.spread_pips} spread = {result.effective_sl_pips} pips"

            def row(label: str, value: str, cls: str = "val") -> str:
                return f'<div class="result-row"><span>{label}</span><span class="{cls}">{value}</span></div>'

            def sep() -> str:
                return '<hr class="sep">'

            lines: list[str] = ['<div class="result-block">']

            lines.append(row("Direction", dir_label, f"val {dir_class}"))
            lines.append(row("Stop Loss", f"{result.stop_loss}  ({sl_label})"))

            if result.tp_pips is not None:
                lines.append(row("Take Profit", f"{result.take_profit}  ({result.tp_pips} pips)"))
                lines.append(row("R:R", f"1:{result.rr_ratio}"))

            lines.append(sep())

            lines.append(row("Risk requested", f"{result.risk_pct}%  (${result.risk_amount:,.2f})"))
            lines.append(row("Effective risk", f"{result.effective_risk_pct:.2f}%  (${result.potential_loss:,.2f})"))

            if result.spread_pips > 0:
                lines.append(row("Spread cost", f"${result.spread_cost:,.2f}"))

            lines.append(sep())

            lines.append(row("Pip value / lot", f"${result.pip_value_per_lot:.4f}"))
            lines.append(row("Position value", f"${result.position_value:,.2f}"))

            if result.potential_profit is not None:
                lines.append(row("Potential profit", f"${result.potential_profit:,.2f}"))

            lines.append('</div>')

            lines.append(f'''
            <div class="lot-block">
                <span class="lot-label">Lot size</span>
                <span class="lot-value">{result.lot_size:.2f}</span>
            </div>
            ''')

            if result.lot_size == 0:
                lines.append('<div style="color:#555;font-size:0.78rem;margin-top:0.4rem">Lot below minimum — reduce SL or increase risk.</div>')

            if result.rate_source:
                lines.append(f'<div class="source-line">rate  {result.rate_source}</div>')

            st.markdown("\n".join(lines), unsafe_allow_html=True)

        except ValueError as e:
            st.error(str(e))
        except KeyError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("<div style='margin-top:3rem;color:#2a2a2a;font-size:0.72rem'>ExchangeRate-API · github.com/saihatex/trading-fx-position-risk-calc</div>", unsafe_allow_html=True)
