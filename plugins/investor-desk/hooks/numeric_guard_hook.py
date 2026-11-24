#!/usr/bin/env python3
"""Load the repository guard for a manually installed local plugin."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

week04 = Path(__file__).resolve().parents[3] / "week04"
sys.path.insert(0, str(week04))
runpy.run_path(str(week04 / "hook_entry.py"), run_name="__main__")
