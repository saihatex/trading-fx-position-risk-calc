# Risk Calculator

Position sizing tool for forex and metals trading. Computes lot size from account risk and trade levels (entry, stop loss, take profit).

Supports multiple broker/prop firm profiles via `config.yaml`, so pip values and contract specs can differ between FTMO, The5ers, FundedNext, or your own setup.

## Features

- Lot size from balance, risk % or fixed cash amount ($), entry, and stop loss price
- Dual risk mode: specify risk in percent (`--risk 1`) or fixed dollars (`--risk-amount 100`)
- Automatic direction detection (long/short)
- Effective risk percentage calculation considering lot size rounding
- Spread inclusion support (`--spread`) in total risk and position sizing
- Stop loss and take profit distance in pips
- Risk/reward ratio from price levels
- Universal dynamic pip value calculation for indirect (`USD/XXX`) and cross pairs (`XXX/YYY`) via conversion rate
- Comprehensive instrument catalog across Forex majors/crosses, metals (`XAUUSD`, `XAGUSD`), indices (`US30`, `NAS100`, `SPX500`, `GER40`), and crypto (`BTCUSD`, `ETHUSD`)

## Install

```bash
pip install -r requirements.txt
```

## Usage

Interactive mode:

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

Example output:

```
Profile:          FTMO
Instrument:       EURUSD
Direction:        LONG

Balance:          $10,000.00
Risk (requested): 1.0% ($100.00)
Effective risk:   0.99% ($98.90)

Entry:            1.085
Stop Loss:        1.083  (20.0 pips + 1.5 spread = 21.5 pips total)
Take Profit:      1.089  (40.0 pips)
R:R:              1:2.0

Pip value / lot:  $10.0000
Lot size:         0.46
Position value:   $46,000.00
Spread cost:      $6.90
Potential loss:   $98.90
Potential profit: $184.00
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
| `pip_value_per_lot` | Account-currency value of one pip at 1.0 lot |

### Dynamic Pip Value Conversions

For pairs where USD is not the quote currency, pass `--quote-rate` (or enter it in interactive mode):
- **Indirect Pairs (`USD/XXX`, e.g. `USDJPY`, `USDCAD`, `USDCHF`)**: Divided by conversion rate.
- **Cross Pairs with JPY/CAD/CHF Quote (e.g. `EURJPY`, `GBPJPY`, `EURCAD`)**: Divided by `USD/YYY` rate.
- **Cross Pairs with GBP/AUD/NZD/EUR Quote (e.g. `EURGBP`, `EURAUD`)**: Multiplied by `YYY/USD` rate (e.g. `GBPUSD` rate for `EURGBP`).

## Tests

```bash
pytest tests/ -v
```

## Known Issues & TODO

- [ ] Add live rate fetching via API (e.g. MetaTrader WebAPI or Yahoo Finance) so quote rate for JPY pairs doesn't need manual input
- [ ] Account currency conversions for non-USD accounts (e.g., EUR/GBP accounts trading USD pairs)
- [ ] Add option to export calculation history to CSV/JSON

## License

MIT
