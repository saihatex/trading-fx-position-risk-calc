# Risk Calculator

Position sizing for forex and metals — runs in your browser, no install required.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://trading-fx-position-risk-calc.streamlit.app)

> **Zero setup for end users:** just open the link above. Live exchange rates fetched automatically.

---

## Run locally

```bash
git clone https://github.com/saihatex/trading-fx-position-risk-calc.git
cd trading-fx-position-risk-calc/risk-calculator
pip install -r requirements.txt
streamlit run app.py
```

## CLI (advanced)

Install once:

```bash
pip install -e .
```

```bash
risk-calc --symbol USDJPY --balance 10000 --risk 1 --entry 163.50 --sl 163.00
```

Or directly:

```bash
python cli.py --interactive
```

CLI with risk percentage:

```bash
python cli.py \
  --profile ftmo \
  --symbol EURUSD \
  --balance 10000 \
  --risk 1 \
  --entry 1.0850 \
  --sl 1.0830 \
  --tp 1.0890 \
  --spread 1.5
```

CLI with fixed cash amount ($150 risk):

```bash
python cli.py \
  --profile ftmo \
  --symbol EURUSD \
  --balance 10000 \
  --risk-amount 150 \
  --entry 1.0850 \
  --sl 1.0830
```

Offline mode (no network requests, uses static values from config.yaml):

```bash
python cli.py \
  --symbol USDJPY \
  --balance 10000 \
  --risk 1 \
  --entry 163.50 \
  --sl 163.00 \
  --no-live-rate
```

Pass a manual rate instead of fetching:

```bash
python cli.py \
  --symbol EURJPY \
  --balance 10000 \
  --risk 1 \
  --entry 178.00 \
  --sl 177.50 \
  --quote-rate 163.75
```

Example output:

```
Profile:          FTMO
Instrument:       USDJPY
Direction:        LONG

Balance:          $10,000.00
Risk (requested): 1.0% ($100.00)
Effective risk:   1.01% ($100.71)

Entry:            163.5
Stop Loss:        163.0  (50.0 pips)

Pip value / lot:  $6.1039  [live: ExchangeRate-API (open.er-api.com) (USDJPY=163.8306)]
Lot size:         0.33
Position value:   $33,000.00
Potential loss:   $100.71
```

## Configuration

Edit `config.yaml` to add or adjust profiles:

```yaml
profiles:
  ftmo:
    label: FTMO
    instruments:
      EURUSD:
        pip_size: 0.0001
        contract_size: 100000
        pip_value_per_lot: 10.0
      XAUUSD:
        pip_size: 0.01
        contract_size: 100
        pip_value_per_lot: 1.0
```

Each profile defines instrument-level:

| Field | Description |
|-------|-------------|
| `pip_size` | Minimum price increment counted as one pip |
| `contract_size` | Units per 1.0 lot |
| `pip_value_per_lot` | Fallback pip value used when `--no-live-rate` is set or API is unreachable |

> **Cache TTL:** live rates are cached for 5 minutes per process. For a long-running service (e.g. Streamlit), use `force_refresh=True` or call `rate_fetcher.clear_cache()` between requests to avoid stale rates.

### Dynamic Pip Value Conversions

For pairs where USD is not the quote currency, the calculator auto-fetches the required rate:
- **Indirect Pairs (`USD/XXX`, e.g. `USDJPY`, `USDCAD`, `USDCHF`)**: `pip_value = contract_size × pip_size / USDXXX_rate`
- **Cross Pairs with JPY/CAD/CHF quote (e.g. `EURJPY`, `GBPJPY`)**: divided by `USD/YYY` rate
- **Cross Pairs with GBP/AUD/NZD/EUR quote (e.g. `EURGBP`, `EURAUD`)**: multiplied by `YYY/USD` rate

You can override the fetched rate with `--quote-rate` or disable fetching entirely with `--no-live-rate`.

## Tests

```bash
python -m pytest tests/ -v
```

## Known Issues & TODO

- [ ] Account currency conversions for non-USD accounts (e.g., EUR/GBP accounts trading USD pairs)
- [ ] Export calculation history to CSV/JSON
- [x] Live exchange rate fetching (v2)
- [x] Entry point `risk-calc` via pyproject.toml (v2)
- [x] TTL cache on live rates (v2)

## License

MIT
