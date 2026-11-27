"""Update the historical summary from saved Phase 0 artifacts."""

import json

from .verify_snapshot import MANIFEST, REFERENCE, ROOT


def render():
    source = json.loads(MANIFEST.read_text())
    metrics = json.loads(REFERENCE.read_text())
    rows = [
        f"The CSV contains {source['raw_rows']:,} raw rows. The California analysis retained "
        f"{metrics['scored_hours']:,} authority-hours and flagged {metrics['high_priority_hours']} for review.",
        "",
        "| Authority | Eligible hours | Mean reported demand (MW) | High-priority hours |",
        "|---|---:|---:|---:|",
    ]
    for authority, data in metrics["by_authority"].items():
        rows.append(f"| {authority} | {data['eligible_hours']:,} | {data['mean_demand_mw']:,.2f} | {data['high_priority_hours']} |")
    return "\n".join(rows)


if __name__ == "__main__":
    path = ROOT / "README.md"
    before, rest = path.read_text().split("<!-- baseline:start -->")
    _, after = rest.split("<!-- baseline:end -->")
    path.write_text(before + "<!-- baseline:start -->\n" + render() + "\n<!-- baseline:end -->" + after)
