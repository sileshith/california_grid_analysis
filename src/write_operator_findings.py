"""Write post-freeze definition findings from generated diagnostic metrics."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    d=json.loads((ROOT/'outputs/metrics/operator_diagnostics.json').read_text())
    v=json.loads((ROOT/'outputs/metrics/forecast_sensitivity.json').read_text())['variants']
    lines=['# Post-freeze operator definition checks','','The seasonal evidence supports retaining demand-definition and alignment caveats. CISO operator forecasts closely match OASIS DAM, while actual demand definitions differ. LDWP model ranking reverses when the sampled EIA target is replaced with OASIS actuals. No full-window superiority claim follows.','','## Local hour, month and shift checks','','Bias is operator forecast minus target demand. At time t, the shift compares the forecast with demand at t plus the stated shift. The saved forecasts are unchanged. Every authority, both demand versions, all local hours and months are recorded in the [diagnostic JSON](../outputs/metrics/operator_diagnostics.json).','','| Authority | Demand version | Shift (h) | Matched hours | Bias (MW) | MAE (MW) |','| --- | --- | ---: | ---: | ---: | ---: |']
    for r in d['diagnostics']:
        if r['authority'] in ['CISO','LDWP']:
            x=r['overall'];lines.append(f"| {r['authority']} | {r['target']} | {r['shift_hours']} | {x['hours']} | {x['bias_mw']:,.2f} | {x['mae_mw']:,.2f} |")
    lines+=['','## Seasonal OASIS comparisons','','Every accepted file contains the expected report item and market, unique complete CAISO hourly coverage, valid timestamps and numeric MW. The two April files were kept. Remaining requests were sequential and spaced by at least the required interval. The [request manifest](../verification/oasis_download_requests.json) records exact URLs, targets, attempts and file hashes.','','| Authority | Market | EIA field | Week start UTC | Hours | Mean absolute difference (MW) | Bias, EIA minus OASIS (MW) |','| --- | --- | --- | --- | ---: | ---: | ---: |']
    for r in d['oasis_comparisons']:
        lines.append(f"| {r['authority']} | {r['market']} | {r['eia_field']} | {r['start']} | {r['matched_hours']} | {r['mae_difference_mw']:,.3f} | {r['bias_eia_minus_oasis_mw']:,.3f} |")
    lines+=['','## Alignment against OASIS actuals','','| Authority | Week start UTC | EIA target shift (h) | Hours | Mean absolute difference (MW) |','| --- | --- | ---: | ---: | ---: |']
    for r in d['oasis_alignment_checks']:
        lines.append(f"| {r['authority']} | {r['start']} | {r['shift_hours']} | {r['hours']} | {r['mae_difference_mw']:,.3f} |")
    lines+=['','CISO agreement improves with the following EIA hour in the spring, summer and autumn samples, but not in winter. This supports an alignment concern and contradicts a single uniform shift as a complete explanation. The sample does not identify the correct publication convention. LDWP discrepancies persist across shifts. No physical storage cause is established.','','## Storage fields and supported proxy','','Exact bulk header names follow. They are preserved verbatim, including source spelling. The holdout files match the frozen source digests.']
    for source in d['storage_headers']:
        lines+=['',f"### {Path(source['path']).name}",'']+[f'- `{c}`' for c in source['columns']]
    lines+=['','Observed dedicated battery-generation values in the saved holdout support: '+', '.join(f"{k}: {n}" for k,n in d['storage_coverage'].items())+'.','','CISO has no observed dedicated battery values, so the dedicated net-generation field cannot supply a CISO correction. The supported exploratory proxy changes LDWP only. Its formula is LDWP adjusted demand plus the minimum of battery net generation and zero. Other authorities retain their original targets. Missing LDWP values remain unavailable. Integrated, pumped and other storage are not removed. Net fleet generation cannot reveal simultaneous gross charging and discharge.','','## Rescoring fixed predictions','','| Variant | G | One-sided upper bound | Common days |','| --- | ---: | ---: | ---: |']
    for name,r in v.items():lines.append(f"| {name} | {r['g']:.6f} | {r['upper95']:.6f} | {r['eligible_days']} |")
    lines+=['','Seasonal variants share the sampled-week baseline. They cannot be interpreted as full-window estimates. Their per-authority ratios and coverage are saved in [forecast_sensitivity.json](../outputs/metrics/forecast_sensitivity.json). Shifted targets also change the loss comparison itself, so a lower G does not validate a clock convention. The frozen headline remains unchanged.']
    (ROOT/'docs/operator_definitions.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
