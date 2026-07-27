# Risk Calculator

Position sizing tool for forex and metals trading. Computes lot size from account risk and trade levels (entry, stop loss, take profit).

Supports multiple broker/prop firm profiles via `config.yaml`, so pip values and contract specs can differ between FTMO, The5ers, FundedNext, or your own setup.

## Features

- Lot size from balance, risk %, entry, and stop loss price
- Automatic direction detection (long/short)
- Stop loss and take profit distance in pips
- Risk/reward ratio from price levels
- Potential loss and profit in account currency
- Broker profiles with per-instrument pip value and contract size
- Lot rounding to broker minimum/step

## Install

```bash
pip install -r requirements.txt
```

## Usage

Interactive mode:

```bash
python cli.py --interactive
```

CLI with arguments:

```bash
python cli.py \
  --profile ftmo \
  --symbol EURUSD \
  --balance 10000 \
  --risk 1 \
  --entry 1.0850 \
  --sl 1.0830 \
  --tp 1.0890
```

Example output:

```
Profile:          FTMO
Instrument:       EURUSD
Direction:        LONG

Balance:          $10,000.00
Risk:             1.0% ($100.00)

Entry:            1.085
Stop Loss:        1.083  (20.0 pips)
Take Profit:      1.089  (40.0 pips)
R:R:              1:2.0

Pip value / lot:  $10.0000
Lot size:         0.50
Position value:   $50,000.00

Potential loss:   $100.00
Potential profit: $200.00
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

For pairs like USDJPY, pass `--quote-rate` or enter it in interactive mode to recalculate pip value dynamically.

## Tests

```bash
pytest tests/ -v
```

## License

MIT
