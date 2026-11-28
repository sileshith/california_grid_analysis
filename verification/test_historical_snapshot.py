"""Opt-in full-snapshot test. Requires the historical CSV and populated SQLite DB."""

import subprocess
import sys

from src.verify_snapshot import ROOT


def test_historical_csv_to_sqlite():
    subprocess.run([sys.executable, "-m", "src.verify_snapshot"], cwd=ROOT, check=True)
