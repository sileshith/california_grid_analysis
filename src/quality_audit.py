"""Profile hourly source versions and explain retrospective queue changes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .transform_energy_metrics import CALIFORNIA_AUTHORITIES, COLUMN_RENAME_MAP

BA = "balancing_authority"
UTC = "utc_time"
FIELDS = dict(COLUMN_RENAME_MAP)
for source in ("Demand (MW)", "Net Generation (MW)", "Total Interchange (MW)"):
    for label in ("Adjusted", "Imputed"):
        FIELDS[f"{source} ({label})"] = FIELDS[source] + "_" + label.lower()


def hourly(raw):
    frame = raw.rename(columns=FIELDS).copy()
    required = list(COLUMN_RENAME_MAP.values())
    missing = set(required) - set(frame)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    frame = frame.loc[frame[BA].isin(CALIFORNIA_AUTHORITIES)].reindex(columns=FIELDS.values())
    frame[UTC] = pd.to_datetime(frame[UTC], utc=True, format="mixed", errors="raise")
    if frame.empty or frame[UTC].isna().any() or (frame[UTC] != frame[UTC].dt.floor("h")).any():
        raise ValueError("Expected nonempty hourly UTC keys")
    keys = [BA, UTC]
    ledger = frame[frame.duplicated(keys, keep=False)].copy()
    counts = frame.groupby(keys).size().rename("source_rows")
    first = frame.drop_duplicates(keys).set_index(keys)
    # A common time extent also reveals leading and trailing gaps.
    calendar = pd.date_range(frame[UTC].min(), frame[UTC].max(), freq="h")
    idx = pd.MultiIndex.from_product([CALIFORNIA_AUTHORITIES, calendar], names=keys)
    first = first.join(counts).reindex(idx)
    first["missing_hour"] = first.source_rows.isna()
    for suffix in ("", "_adjusted"):
        first["balance_residual" + suffix] = (first["demand_mw" + suffix]
            - first["net_generation_mw" + suffix] + first["total_interchange_mw" + suffix])
    return first.reset_index(), ledger


def audit(raw):
    frame, ledger = hourly(raw)
    summary = {}
    changes = []
    for ba, rows in frame.groupby(BA):
        paired = rows.dropna(subset=["demand_mw", "demand_mw_adjusted"]).copy()
        reported = paired.demand_mw
        adjusted = paired.demand_mw_adjusted
        peaks = [reported.max(), reported.max(), adjusted.max()]
        names = ["reported", "adjusted_fixed_peak", "adjusted"]
        for name, values, peak in zip(names, [reported, adjusted, adjusted], peaks):
            paired[name] = ((100 * values / peak).round(2) >= 90) if peak > 0 else False
        prior = rows.demand_mw.shift(1).rolling(168, min_periods=168).quantile(.99)
        candidate = rows.demand_mw / prior.where(prior > 0)
        flags = paired[names]
        union = paired.reported | paired.adjusted
        changed = paired.reported ^ paired.adjusted
        summary[ba] = {
            "calendar_hours": len(rows), "missing_hours": int(rows.missing_hour.sum()),
            "null_reported": int((~rows.missing_hour & rows.demand_mw.isna()).sum()),
            "zero_reported": int(rows.demand_mw.eq(0).sum()),
            "duplicate_keys": int(rows.source_rows.gt(1).sum()),
            "changed_readings": int(reported.ne(adjusted).sum()), "eligible": len(paired),
            "reported_peak": None if paired.empty else float(peaks[0]),
            "adjusted_peak": None if paired.empty else float(peaks[-1]),
            "queue_counts": [int(n) for n in flags.sum()], "shared": int((paired.reported & paired.adjusted).sum()),
            "changed_share": float(changed.sum()/union.sum()) if union.any() else None,
            "prior_week_p99_eligible": int(candidate.count()), "at_or_above_prior_p99": int(candidate.ge(1).sum()),
        }
        for suffix in ("", "_adjusted"):
            residual = rows["balance_residual" + suffix]
            summary[ba]["balance" + suffix] = {"eligible": int(residual.count()),
                "above_1_mw": int(residual.abs().gt(1).sum()), "above_10_mw": int(residual.abs().gt(10).sum())}
        changes.append(paired.loc[flags.any(axis=1), [BA, UTC, "demand_mw", "demand_mw_adjusted", *names]])
    return summary, pd.concat(changes), frame, ledger


def run(paths, out):
    parts = []
    hashes = []
    for path in paths:
        hashes.append({"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        parts.append(pd.read_csv(path, usecols=lambda c:c in FIELDS, low_memory=False))
    stats, flags, frame, duplicates = audit(pd.concat(parts, ignore_index=True))
    out.mkdir(parents=True, exist_ok=True)
    payload = {"sources":hashes,"authorities":stats}
    (out / "quality_audit.json").write_text(json.dumps(payload, indent=2, allow_nan=False)+"\n")
    frame.to_parquet(out / "hourly.parquet", index=False)
    duplicates.to_parquet(out / "duplicate_observations.parquet", index=False)
    flags.to_csv(out / "queue_membership.csv",index=False)
    lines = ["# Historical demand quality audit", "", "Counts use shared observed reported and adjusted hours for queue membership. Missing hours use the common source time extent. Flags can overlap.", "",
             "| Authority | Paired hours | Missing hours | Observed zeros | Reported queue | Adjusted at fixed peak | Adjusted queue | Shared |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for ba,s in stats.items():
        lines.append("| "+" | ".join(map(str,[ba,s["eligible"],s["missing_hours"],s["zero_reported"],*s["queue_counts"],s["shared"]]))+" |")
    (out / "quality_audit.md").write_text("\n".join(lines)+"\n")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.csv, args.out)
