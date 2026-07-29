# Risk Calculator

Position sizing for forex and metals trading with live exchange rates.

[**Web App**](https://trading-fx-position-risk-calc.streamlit.app) · [**CLI Usage**](#cli)

---

## Features

- **Live Exchange Rates**: Auto-converts pip values for indirect (`USDJPY`) and cross pairs (`EURJPY`, `EURGBP`) using ExchangeRate-API (5 min TTL cache).
- **Flexible Sizing**: Risk by percentage (`1%`) or fixed dollar amount (`$100`).
- **Broker Specs**: Configurable contract sizes, pip sizes, and profiles (`config.yaml`).
- **Spread Support**: Includes spread in total pips and risk calculation.

---

## Web App

Run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## CLI

Install CLI entry point:

```bash
pip install -e .
risk-calc --symbol USDJPY --balance 10000 --risk 1 --entry 163.50 --sl 163.00
```

Interactive CLI:

```bash
risk-calc --interactive
```

---

## Configuration

Custom broker profiles and static fallbacks in `config.yaml`:

```yaml
profiles:
  ftmo:
    label: FTMO
    instruments:
      EURUSD: { pip_size: 0.0001, contract_size: 100000, pip_value_per_lot: 10.0 }
      USDJPY: { pip_size: 0.01, contract_size: 100000, pip_value_per_lot: 6.67 }
      XAUUSD: { pip_size: 0.01, contract_size: 100, pip_value_per_lot: 1.0 }
```

---

## Testing

```bash
python -m pytest tests/ -v
```

---

## License

MIT
