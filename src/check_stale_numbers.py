"""Scan only the requested publication paths for superseded headline numbers."""
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
# Prior README model/accuracy claims, superseded by the frozen matched benchmark.
PATTERNS = {
    'old_lightgbm_mape': r'(?<![\d.])3\.29(?![\d.])',
    'old_naive_mape': r'(?<![\d.])11\.05(?![\d.])',
    'old_prophet_mape': r'(?<![\d.])16\.8(?![\d.])',
    'old_mean_correlation': r'(?<![\d.])0\.484(?![\d.])',
    'old_spatial_penalty': r'(?<![\d.])5\.5\s*%',
    'old_test_count': r'\b36\s+(?:tests|pytest|automated|passing)\b',
    'old_verification_number': r'\b10\.0\.1\b',
}


def inspect():
    paths = [ROOT / 'README.md', ROOT / 'notebooks/release_results.ipynb']
    for directory in ('docs', 'reports'):
        paths.extend(sorted((ROOT / directory).rglob('*')))
    # Only tracked/publication inputs; PNG previews and binary fonts aren't prose.
    paths = [p for p in paths if p.is_file() and 'previews' not in p.parts]
    findings = []
    scanned = []
    for path in paths:
        if path.suffix == '.pdf':
            content = '\n'.join(p.extract_text() for p in PdfReader(path).pages)
        else:
            try:
                content = path.read_text()
            except (UnicodeError, OSError):
                continue
        name = path.relative_to(ROOT).as_posix()
        scanned.append(name)
        for label, pattern in PATTERNS.items():
            for number, line in enumerate(content.splitlines(), 1):
                if re.search(pattern, line, re.I):
                    findings.append(dict(path=name, line=number, pattern=label))
    return dict(
        scope=['README.md', 'docs/', 'reports/', 'notebooks/release_results.ipynb'],
        patterns=PATTERNS,
        scanned_files=scanned,
        findings=findings,
        note='Checks superseded README accuracy/spatial/test claims and old section numbering. '
             'PDF text is extracted; binary fonts and local preview images are skipped. '
             'Historical snapshot counts and explicitly historical roadmap figures are retained. '
             'This is a targeted stale-claim scan, not validation of every number in every document.',
    )


if __name__ == '__main__':
    result = inspect()
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['findings']))
