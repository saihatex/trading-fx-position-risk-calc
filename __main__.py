import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cli import main  # noqa: E402

sys.exit(main())
