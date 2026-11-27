import json

from src.render_baseline import render
from src.verify_snapshot import MANIFEST, REFERENCE, ROOT


def test_published_snapshot_matches_reference():
    manifest = json.loads(MANIFEST.read_text())
    metrics = json.loads(REFERENCE.read_text())
    assert manifest["sha256"] == metrics["input_sha256"]
    assert sum(manifest["raw_rows_by_authority"].values()) == manifest["raw_rows"]
    assert sum(row["eligible_hours"] for row in metrics["by_authority"].values()) == metrics["scored_hours"]
    assert sum(row["high_priority_hours"] for row in metrics["by_authority"].values()) == metrics["high_priority_hours"]
    published = (ROOT / "README.md").read_text().split("<!-- baseline:start -->")[1].split("<!-- baseline:end -->")[0]
    assert published.strip() == render()
