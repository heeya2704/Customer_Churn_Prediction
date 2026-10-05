"""Reproduce the production model: ``python training/train.py``.

Run from the repository root. All training logic lives in ``app.ml.train`` so
it stays importable and testable; this script only wires up the import path.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.train import main  # noqa: E402

if __name__ == "__main__":
    main()
