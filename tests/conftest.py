from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / 'app'

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
