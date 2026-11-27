"""Acquire the published half-year files while preserving every distinct vintage."""
import hashlib
import json
import tempfile
from pathlib import Path

import requests


def main():
    manifest=json.loads(Path("data/manifest/benchmark_sources.json").read_text())
    root=Path("data/raw/history")
    root.mkdir(parents=True,exist_ok=True)
    for source in manifest:
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            stage=Path(tmp)/source["file"]
            with requests.get(source["url"],timeout=(15,120),stream=True) as response:
                response.raise_for_status()
                with stage.open("wb") as output:
                    for chunk in response.iter_content(1024*1024):
                        output.write(chunk)
            digest=hashlib.sha256(stage.read_bytes()).hexdigest()
            target=root/digest/source["file"]
            target.parent.mkdir(exist_ok=True)
            stage.replace(target)
            print(target, "matches frozen input" if digest==source["sha256"] else "revised source")
if __name__=="__main__":
    main()
