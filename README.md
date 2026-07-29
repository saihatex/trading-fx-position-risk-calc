# Risk Calculator

Position sizing tool for forex and metals trading. Computes lot size from account risk and trade levels (entry, stop loss, take profit).

Supports multiple broker/prop firm profiles via `config.yaml`, so pip values and contract specs can differ between FTMO, The5ers, FundedNext, or your own setup.

> **Network note:** by default the calculator fetches a live exchange rate for any pair that needs currency conversion (e.g. USDJPY, EURJPY, USDCAD). This requires an internet connection. Pass `--no-live-rate` to work fully offline — the tool will fall back to the static `pip_value_per_lot` value from `config.yaml`.

## Features

- Lot size from balance, risk % or fixed cash amount ($), entry, and stop loss price
- Dual risk mode: specify risk in percent (`--risk 1`) or fixed dollars (`--risk-amount 100`)
- Automatic direction detection (long/short)
- Effective risk percentage calculation considering lot size rounding
- Spread inclusion support (`--spread`) in total risk and position sizing
- Stop loss and take profit distance in pips
- Risk/reward ratio from price levels
- Live pip value calculation via free exchange rate APIs (`open.er-api.com` / `frankfurter.app`) with automatic fallback
- Universal dynamic pip value for indirect (`USD/XXX`) and cross pairs (`XXX/YYY`)
- Comprehensive instrument catalog across Forex majors/crosses, metals (`XAUUSD`, `XAGUSD`), indices (`US30`, `NAS100`, `SPX500`, `GER40`), and crypto (`BTCUSD`, `ETHUSD`)

## Install

Dev install (editable, installs `risk-calc` entry point):

```bash
pip install -e .
```

Or just install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Via entry point (after `pip install -e .`):

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
