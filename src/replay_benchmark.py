"""Replay immutable frozen code in a disposable local clone and compare bytes."""
import argparse
import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replay(freeze_ref="spec-frozen-v1"):
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", freeze_ref + "^{commit}"], cwd=ROOT,
        text=True,
    ).strip()
    expected = (ROOT / "outputs/metrics/forecast_benchmark.json").read_bytes()
    with tempfile.TemporaryDirectory(prefix="grid-replay-") as temporary:
        clone = Path(temporary) / "checkout"
        subprocess.run(["git", "clone", "--no-hardlinks", str(ROOT), str(clone)], check=True)
        subprocess.run(["git", "checkout", "--detach", commit], cwd=clone, check=True)
        # The immutable scorer resolves this historical name. Bind it only inside
        # the disposable clone so any explicit freeze reference can be checked.
        subprocess.run(["git", "update-ref", "refs/tags/spec-frozen-v1", commit], cwd=clone, check=True)
        target = clone / ".artifacts/benchmark/hourly.parquet"
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".artifacts/benchmark/hourly.parquet", target)
        subprocess.run([sys.executable, "-m", "src.benchmark", "score"], cwd=clone, check=True)
        actual = (clone / "outputs/metrics/forecast_benchmark.json").read_bytes()
        if actual != expected:
            print("".join(difflib.unified_diff(
                expected.decode().splitlines(keepends=True),
                actual.decode().splitlines(keepends=True),
                fromfile="published", tofile="replayed",
            )))
            raise ValueError("Replay differs from published forecast_benchmark.json")
    print(f"PASS: {commit} reproduces forecast_benchmark.json byte for byte")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-ref", default="spec-frozen-v1")
    replay(parser.parse_args().freeze_ref)
