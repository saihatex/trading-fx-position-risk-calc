from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main(argv: list[str] | None = None) -> int:
    from risk_calc.cli import main as cli_main
    return cli_main(argv)
