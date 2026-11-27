"""Reproduce the historical CSV contract and verify the local SQLite outputs."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from .calculate_grid_stress_index import calculate_grid_stress_index
from .transform_energy_metrics import transform_energy_metrics
from .validate_grid_data import validate_grid_data

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifest/eia930-9b0b83506002.json"
REFERENCE = ROOT / "outputs/metrics/historical_baseline.json"


def describe(csv_path):
    with csv_path.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    raw = pd.read_csv(csv_path, low_memory=False)
    validated, _ = validate_grid_data(raw)
    scored = calculate_grid_stress_index(transform_energy_metrics(validated))
    utc = pd.to_datetime(raw["UTC Time at End of Hour"], utc=True)
    by_authority = {}
    for authority, rows in scored.groupby("balancing_authority"):
        by_authority[authority] = {
            "eligible_hours": len(rows),
            "high_priority_hours": int(rows["review_priority"].eq("High Review Priority").sum()),
            "mean_demand_mw": round(float(rows["demand_mw"].mean()), 2),
            "first_utc": rows["utc_time"].min().isoformat(),
            "last_utc": rows["utc_time"].max().isoformat(),
        }
    manifest = {
        "filename": csv_path.name, "sha256": checksum, "size_bytes": csv_path.stat().st_size,
        "retrieval_date": None, "source_mode": "EIA-930 bulk CSV",
        "raw_rows": len(raw), "fields": list(raw.columns),
        "first_utc": utc.min().isoformat(), "last_utc": utc.max().isoformat(),
        "raw_rows_by_authority": raw["Balancing Authority"].value_counts().sort_index().to_dict(),
    }
    metrics = {
        "input_sha256": checksum, "scored_hours": len(scored),
        "high_priority_hours": sum(row["high_priority_hours"] for row in by_authority.values()),
        "by_authority": by_authority,
    }
    return manifest, metrics


def verify_database(path, metrics):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
        for table, field in [("grid_hourly_metrics", "eligible_hours"),
                             ("grid_stress_scores", "eligible_hours"),
                             ("high_priority_review_queue", "high_priority_hours")]:
            counts = dict(conn.execute(f"SELECT balancing_authority, COUNT(*) FROM {table} GROUP BY balancing_authority"))
            expected = {ba: row[field] for ba, row in metrics["by_authority"].items() if row[field]}
            if counts != expected:
                raise ValueError(f"{table}: expected {expected}, found {counts}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--database", type=Path, default=ROOT / "outputs/grid_operations.db")
    args = parser.parse_args()
    expected = json.loads(MANIFEST.read_text())
    csv_path = args.csv or ROOT / "data/raw" / expected["filename"]
    if not csv_path.is_file():
        parser.error(f"Missing historical CSV at {csv_path}. Required SHA-256: {expected['sha256']}")
    with csv_path.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != expected["sha256"]:
            parser.error("Snapshot checksum differs from the historical manifest.")
    manifest, metrics = describe(csv_path)
    if manifest != expected or metrics != json.loads(REFERENCE.read_text()):
        raise ValueError("Historical source profile or scored results differ from the reference.")
    if not args.database.is_file():
        parser.error("Missing SQLite output. Run the standalone pipeline first.")
    verify_database(args.database, metrics)
    print(f"Verified {metrics['scored_hours']:,} scored hours and {metrics['high_priority_hours']} flags.")


if __name__ == "__main__":
    main()
