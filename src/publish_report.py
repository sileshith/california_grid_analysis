"""Publish release prose and reproduction artifacts from metric JSON evidence."""
import json
from pathlib import Path
from .render_baseline import render
from .make_figures import generate as make_figures

ROOT=Path(__file__).resolve().parents[1]
MET=ROOT/'outputs/metrics'


def read(name):return json.loads((MET/name).read_text())


def generate():
    s=read('forecast_benchmark.json');q=read('quality_audit.json')['authorities'];e=read('event_validation.json');d=read('operator_diagnostics.json');v=read('forecast_sensitivity.json')['variants'];replay=read('replay_audit.json')
    spec=json.loads((ROOT/'config/holdout.json').read_text());frozen=json.loads((ROOT/'config/frozen_benchmark.json').read_text())
    model=s['candidate'];ub=s['upper95'][str(s['block_days'])]
    rows={(r['balancing_authority'],r['method']):r for r in s['authority_metrics']}
    baseline=render()
    def diagnostic(ba,shift=0,target='adjusted'):return next(r for r in d['diagnostics'] if r['authority']==ba and r['shift_hours']==shift and r['target']==target)
    c=diagnostic('CISO');ld=diagnostic('LDWP')
    headline=f"Across {s['eligible_days']} matched delivery days, the geometric mean of the five authority-level model-to-operator MAE ratios was {s['g']:.3f}, with a one-sided 95% upper bound of {ub:.3f}. A ratio of 1 denotes parity. The result supports retaining the operator forecasts across the five authorities. The model recorded lower mean daily errors for CISO ({rows['CISO',model]['daily_mae_mw']:,.0f} versus {rows['CISO','authority']['daily_mae_mw']:,.0f} MW) and LDWP ({rows['LDWP',model]['daily_mae_mw']:,.0f} versus {rows['LDWP','authority']['daily_mae_mw']:,.0f} MW), but interpreting those differences requires checking demand definitions and hour alignment."
    queue=f"BANC's retrospective queue changed from {q['BANC']['queue_counts'][0]} to {q['BANC']['queue_counts'][1]} to {q['BANC']['queue_counts'][2]} flagged hours as adjusted readings and then the revised peak were applied."
    event_runs=[r for r in e['runs'] if r['field']=='adjusted' and r['review_budget']==12]
    event_sentence=' '.join(f"In {r['start'][:4]}, both rules captured {len(r['rules']['demand']['hits'])} of {len(r['documented_event_days'])} catalog event days at a {r['review_budget']}-day review budget." for r in event_runs)+' Recall is undefined when no qualifying event exists.'
    oasis_forecast=[r['mae_difference_mw'] for r in d['oasis_comparisons'] if r['authority']=='CISO' and r['market']=='DAM']
    oasis_actual=[r['mae_difference_mw'] for r in d['oasis_comparisons'] if r['authority']=='CISO' and r['eia_field']=='actual']
    oasis_finding=f"Across the seasonal weeks, CISO EIA forecasts agree with OASIS DAM within {min(oasis_forecast):.2f}-{max(oasis_forecast):.2f} MW mean absolute difference, but adjusted actuals differ by {min(oasis_actual):,.0f}-{max(oasis_actual):,.0f} MW. LDWP's sampled ratio changes from {v['seasonal_original_adjusted']['ratios']['LDWP']:.3f} to {v['seasonal_oasis_actual']['ratios']['LDWP']:.3f} when OASIS actuals replace its EIA target. This supports a demand-definition caveat, not a superiority claim."
    caveat=f"The post-freeze shift check lowers CISO operator hourly MAE from {c['overall']['mae_mw']:,.1f} to {diagnostic('CISO',1)['overall']['mae_mw']:,.1f} MW when demand is taken from the following UTC hour. This does not establish the correct timestamp convention. {oasis_finding}"
    table=['| Authority | Model daily MAE (MW) | Operator daily MAE (MW) | Ratio |','| --- | ---: | ---: | ---: |']
    for ba in sorted(q):
        a=rows[ba,model]['daily_mae_mw'];b=rows[ba,'authority']['daily_mae_mw'];table.append(f'| {ba} | {a:,.1f} | {b:,.1f} | {a/b:.3f} |')
    table='\n'.join(table)
    variants=['| Post-freeze target variant | G | Upper bound | Days |','| --- | ---: | ---: | ---: |']
    for name,r in v.items():variants.append(f"| {name.replace('_',' ')} | {r['g']:.3f} | {r['upper95']:.3f} | {r['eligible_days']} |")
    variants='\n'.join(variants)
    cross=['| Authority and field | Season | Hours | EIA minus OASIS bias (MW) | Mean absolute difference (MW) |','| --- | --- | ---: | ---: | ---: |']
    for r in d['oasis_comparisons']:
        if r['eia_field']=='actual':cross.append(f"| {r['authority']} adjusted demand | {r['start'][:8]} | {r['matched_hours']} | {r['bias_eia_minus_oasis_mw']:,.1f} | {r['mae_difference_mw']:,.1f} |")
    cross='\n'.join(cross)
    block=', '.join(f"{k}-day blocks: {value:.3f}" for k,value in sorted(s['upper95'].items(),key=lambda x:int(x[0])))
    sections=[]
    def section(title,text):sections.append((title,text.strip()))
    section('Business questions and decisions',f'''The release supports retaining operator forecasts and auditing demand definitions before considering a model shadow trial. {headline}

The hiring decision this project informs is whether the analysis can connect a statistical comparison with an operational choice and a reproducible data contract. The forecast comparison asks whether a local issue-time model improves proportional error across the California authorities. A separate revision question asks which hours enter or leave a retrospective review queue when EIA changes demand. The event question asks whether a composite daily ranking captures documented alerts at the same review workload as a demand-only rule.

{queue} {event_sentence}

No adoption margin has been specified. The frozen comparison does not justify deployment. The review queue is an analyst workload device. A high score does not establish an emergency or causation.''')
    related='''Seasonal naive forecasts and chronological evaluation provide a transparent benchmark ladder. Hyndman and Athanasopoulos (2021) explain why forecasting methods should be assessed against simple comparators using genuinely later observations. Here the operator forecast is the primary comparator, while a previous-week local-hour rule and a trailing moving average help interpret the learned candidate. The project retains per-authority errors because proportional summaries can obscure the size of MW differences.

Kunsch (1989) develops block resampling for dependent observations. The release applies contiguous delivery-day blocks jointly across authorities so the resampled comparison retains within-block temporal and cross-authority pairing. That methodological precedent does not verify this dataset's stationarity. Block-length sensitivity and the amount of usable history remain part of the interpretation.

EIA's Hourly Electric Grid Monitor documentation is operational gray literature. It describes a physical accounting dataset subject to reporting and adjustment conventions. CAISO's OASIS documentation distinguishes actual demand and market-process forecasts. Those sources motivate checking definitions before interpreting a lower model error as a forecasting advantage. The current bulk headers expose net battery-generation fields, but net output alone cannot identify simultaneous gross charging and discharging across a fleet.

The event-history catalog is also gray literature. Its alert notices supply externally documented labels rather than a validation target constructed from the demand score itself. A small catalog limits any ranking comparison. A transmission-related watch may occur without unusually high demand, so missing a label can reveal a mechanism mismatch rather than a threshold error.

The requested reviewed literature source is unavailable. The [full-review status](literature_review.md) records this missing input. No wording or references from the absent review have been reconstructed. The verified bibliography below covers only the methodological and operational sources used in this report.'''
    section('Related work',related)
    section('Data and provenance',f'''The forecast comparison uses archived EIA bulk vintages whose digests are recorded in the [source manifest](../data/manifest/benchmark_sources.json). The saved hourly parquet matches the published freeze hash. The separate historical quality snapshot has its own manifest and is not interchangeable with the forecast study's later bulk inputs.

The frozen test begins {s['start']} and ends before {s['end_exclusive']}. It contains {s['intended_hours']:,} intended authority-hours. Eligibility leaves {s['matched_hours']:,} matched hours across {s['eligible_days']} common delivery days. Missing observations are not silently filled for evaluation. Source anomalies are flagged and retained. Duplicate handling and observed zeros are explicit quality categories.

Post-freeze OASIS downloads cover spring, summer, autumn and winter weeks. Every accepted ZIP was checked for its report item, market identifier, unique hourly CAISO timestamps, numeric MW values and complete requested coverage. HTTP success alone was insufficient. Raw inputs stay outside version control. The download manifest records request attempts, response outcomes and hashes. The holdout EIA files retrieved for storage checks match their frozen source digests.

Acquisition code first appears in the scoring commit and is outside the frozen code-hash list. The freeze tag was added after scoring and establishes replay resolution, not the time of scoring. See [freeze scope](freeze_scope.md).''')
    section('Quality audit and sequential attribution',f'''{queue} This sequential calculation separates a reading change from a threshold change. It avoids attributing every membership difference to the observation alone.

RQ2 uses authority-hours with both reported and adjusted demand in the historical snapshot. The initial queue divides reported demand by the reported peak, rounds the percentage to two decimals, and applies the fixed threshold. The intermediate queue substitutes adjusted demand while holding that original peak fixed. The final queue also substitutes the adjusted peak. Each transition reports retained, entered and exited hours.

The BANC reported peak is {q['BANC']['reported_peak']:,.0f} MW and the adjusted peak is {q['BANC']['adjusted_peak']:,.0f} MW. A revised maximum changes the denominator for every eligible hour. The final queue can therefore grow after the anomalous reported spike is corrected. This is a property of the retrospective rule and does not establish a change in actual operational risk.

The audit distinguishes missing calendar hours, observed nulls, zeros and conflicting duplicates. Balance residuals compare demand, net generation and interchange under each target version. Imbalance or a revision is flagged for interpretation rather than deleted to improve a score. The historical queue evidence remains separate from the later full-window forecast evaluation.''')
    section('Methodology: issue time and predictors',f'''The forecast issue is {spec['issue_hour_pacific']}:00 Pacific on the day before delivery. UTC hour-ending keys identify intervals. Their Pacific start date defines the delivery day. This preserves the actual intervals on daylight-saving clock changes instead of forcing every day into a constant-length grid.

The availability assumption subtracts {spec['assumed_reporting_delay_hours']} hour from issue time before selecting recent observations. It is an assumption about reporting delay, not evidence that each archived observation was available in that version at that instant. Retrospective bulk revisions can enter historical predictors without vintage proof. The operator forecast is likewise an archived comparator whose original publication-time availability has not been established by the bulk file alone.

Calendar predictors encode delivery hour, weekday and issue-to-target horizon. Demand features include the comparable previous-week local time, a trailing mean and the last available reading at the cutoff. Weekly lookup handles ambiguous or nonexistent wall-clock times as unavailable. The learned models train on reported historical demand. The retrospective primary target is adjusted demand. The saved predictions permit alternative target scoring without retraining.

Training is restricted to outcomes before the earliest issue-time cutoff in the next evaluation window. The complete last validation delivery day is discarded because its outcomes would otherwise arrive after the first test issue. This prevents an obvious boundary leak but cannot restore missing publication vintages. A change to availability policy would require a new development experiment rather than a revision to the frozen result.''')
    section('Methodology: windows, selection and inference',f'''Candidate selection uses the chronological development window beginning {spec['validation_start']} and ending before {spec['test_start']}. The candidate pool is {', '.join(spec['candidate_pool'])}. The frozen development selection chose {model}. Model rank is an observed result. No candidate is promoted by deleting unfavorable authority outcomes.

For each eligible authority and delivery day, the calculation averages absolute errors on identical matched target hours. It then averages daily MAE across common days. The authority ratio divides the candidate mean daily MAE by the operator mean daily MAE. G is the exponential of the mean log ratio across authorities. Each authority has equal proportional weight, and each eligible day has equal weight within an authority. This differs from pooling all MW errors, which would give large systems a larger influence.

Eligibility requires at least {spec['minimum_daily_fraction']:.0%} of the actual delivery-day intervals with all comparator methods and the target observed. All authorities must have an eligible day for the joint panel. Undefined or nonpositive ratios prevent log-based inference. Coverage is reported beside the score so a favorable result cannot conceal selective exclusions.

The moving-block bootstrap resamples contiguous eligible delivery-day blocks jointly across authorities and recomputes the ratios and G. There are {spec['replicates']:,} replicates with seed {spec['seed']}. The upper bound uses the {spec['confidence']:.0%} quantile. Development loss autocorrelation selected {frozen['block_days']}-day blocks. The frozen block-length sensitivity is {block}. A bound above parity does not support the deployment claim.''')
    section('Methodology: revisions, events and definitions',f'''Post-freeze sensitivity holds the saved forecasts fixed and changes the target or alignment. Adjusted and reported demand are scored separately. At forecast time t, a negative shift uses demand at an earlier UTC hour. Endpoint loss can alter common eligible days, so each variant reports its own coverage. The shift is a diagnostic and does not decide the correct clock convention.

The LDWP-only storage proxy adds the negative part of battery net generation to adjusted demand. Other authorities retain their original targets. CISO has no observed dedicated battery-generation values in the holdout bulk fields, so a CISO storage correction is unsupported. This removes net charging only when aggregate battery generation is negative. It cannot recover gross charging, does not handle simultaneous fleet charging and discharge, and does not subtract integrated, pumped or other storage. It is labeled exploratory. Official reporting instructions and implementation-specific definitions must be reconciled before treating it as a corrected target.

OASIS actual and DAM reports are compared on interval-ending UTC keys. CA ISO-TAC maps to CISO and LADWP maps to LDWP. The seasonal comparison changes only these authorities' target and optionally their operator forecast. Other authorities retain their EIA values. Those sampled-week G values are compared with a sampled-week baseline, not with the full-window headline.

Event validation uses trailing observations for normalization. The day score is the maximum hourly score, and a daily coverage rule excludes sparse days. Demand-only and composite rules select the same review budget in each annual window under reported and adjusted demand. The composite weights demand normalization, import reliance and forecast surprise. These same-day inputs support retrospective screening, not a day-ahead alert claim. Catalog coverage is checked, missed labels are retained, and recall is undefined for a year without qualifying events.''')
    section('Results: frozen headline',f'''{headline}

{table}

Coverage is {s['matched_hours']:,} matched authority-hours from {s['intended_hours']:,} intended over {s['eligible_days']} matched delivery days. Reported-demand sensitivity gives G = {s['reported_target_g']:.3f}. The upper bound remains above parity, so changing the retrospective target does not provide systemwide adoption evidence.

![Figure 1. Relative error favors retaining the operator forecasts in the aggregate. The orange interval connects G to its one-sided upper bound. Source: forecast_benchmark.json.](../assets/figures/relative_mae.png)

{queue} The queue result is descriptive and concerns the separate historical quality snapshot.''')
    section('Results: post-freeze sensitivity',f'''{caveat}

{variants}

The storage proxy and shifted targets do not change the published headline. Seasonal OASIS substitutions have a different support from the full-window comparison. Their per-authority ratios and coverage are available in the [sensitivity JSON](../outputs/metrics/forecast_sensitivity.json).

CISO operator mean bias is {c['overall']['bias_mw']:,.1f} MW and LDWP mean bias is {ld['overall']['bias_mw']:,.1f} MW under adjusted demand. Persistent level and hour-of-day differences support further definition checks. They do not establish which demand convention should be used.

![Figure 2. CISO operator bias varies by local delivery hour, motivating alignment and definition checks. Source: operator_diagnostics.json.](../assets/figures/ciso_bias.png)

{event_sentence} The event catalog is too sparse to establish detector superiority.''')
    section('Limitations and ethical considerations',f'''The strict full-JSON frozen replay fails in the tested environment. Two repeated fits are {'identical' if replay['repeat_byte_identical'] else 'different'} within that environment. Only Prophet authority metrics differ from the publication. LightGBM, authority, previous-week, moving-average and headline fields match exactly. The fit sets no explicit Prophet seed or thread count. The original runtime is unavailable and the cause remains unresolved. The published JSON has been preserved.

The retrospective source archive cannot establish original release-time availability. Adjusted targets can differ from operationally observed demand. The storage proxy cannot identify a physically complete demand correction. Hour shifts can reduce error simply by aligning recurring shapes differently. Seasonal OASIS checks are a limited sample rather than a full-period reconstruction.

Small authorities have equal proportional weight in G. This is a stated decision metric rather than a claim about total system MW impact. The adoption margin remains unspecified. Peak-hour performance and coverage must accompany the aggregate. A sparse alert catalog prevents stable precision or recall comparisons, and transmission-driven events need predictors beyond demand.

The analysis uses public aggregate operational records and contains no customer-level demand. Its main ethical risk is overstating reliability, emergency detection or model readiness. Preserve flagged anomalies, disclose missing forecasts, separate unavailable output from zero demand, and retain source revisions for audit. Avoid presenting a retrospective score as a dispatch recommendation or a warning service.''')
    section('Engineering, monitoring and next steps',f'''The release demonstrates isolated fixture execution and transactional interval publication. The [component inventory](component_port_plan.md) records paths and dependencies from the verified bundle. Files were copied individually without merging histories. Frozen benchmark files, published metrics and replay checks were preserved.

The interval stage requires unique complete authority-hour coverage within a half-open UTC interval. A manifest hashes the staged payload. Publication uses one transaction for revision history, current values and batch metadata. An injected failure leaves prior data intact. A retry publishes the complete interval, and an older replay cannot supersede a newer vintage. The forecast-status table separately records unavailable output and timely authority fallback.

The interval DAG was imported in the local Airflow environment and its dependency edge was checked. This is not evidence of continuous service operation. Docker Compose is supplied but Docker is unavailable locally. Network PostgreSQL and hosted CI remain unverified here. CI declares the fixture suite, a PostgreSQL contract job and the PDF build. The [implementation audit](implementation_audit.md) records current execution evidence.

Monitoring should track the most recent complete publication, expected authority-hours, duplicate and null counts, source-vintage changes, unavailable forecasts and operator fallback latency. Investigate definition drift when persistent hourly bias changes. Retain separate target-version dashboards rather than mixing revised and reported demand.

Next steps are to supply the reviewed literature source, recover the original Prophet runtime, reconcile the supported demand definition with source owners, and review publication before any push. Hosted CI, a GitHub-rendered preview and service uptime can be checked only in their respective environments.''')
    refs='''California Independent System Operator. (n.d.). *OASIS frequently asked questions* [Technical documentation, gray literature]. https://www.caiso.com/documents/oasis-frequently-asked-questions.pdf

California Independent System Operator. (2026). *Grid emergencies history report: 1998 to present* [Operational history, gray literature]. https://www.caiso.com/documents/grid-emergencies-history-report-1998-to-present.pdf

Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/

Kunsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. *The Annals of Statistics, 17*(3), 1217-1241. https://doi.org/10.1214/aos/1176347265

U.S. Energy Information Administration. (n.d.). *About the Hourly Electric Grid Monitor* [Technical documentation, gray literature]. https://www.eia.gov/electricity/930-content/about.html'''
    section('References',refs)
    report='# California grid analytics report\n\n'+'\n\n'.join('## '+title+'\n\n'+text for title,text in sections)+'\n'
    (ROOT/'docs/report.md').write_text(report)
    readme=f'''# California Grid Analytics

Audited demand revisions, day-ahead forecast comparisons and reproducible interval operations.

### Executive summary

{headline}

{queue} {event_sentence}

{caveat}

### Results

{table}

![Relative MAE by authority](assets/figures/relative_mae.png)

The aggregate ratio and its upper bound support retaining operator forecasts.

![CISO operator bias by local hour](assets/figures/ciso_bias.png)

The hourly bias pattern requires demand-definition and timestamp checks before interpreting CISO model gains.

### Reproduce

```bash
python -m pip install -r requirements-release.txt
make demo
make report
```

The demo creates isolated synthetic inputs, runs the pipeline and executes the tests. Reports read saved metric JSON. Archived inputs are needed for the strict frozen replay:

```bash
python -m src.replay_benchmark --freeze-ref spec-frozen-v1
```

### Pipeline and repository map

```mermaid
flowchart LR
  A[EIA vintages and manifests] --> B[Validate and flag]
  B --> C[Transactional interval store]
  B --> D[Frozen forecasts and paired evaluation]
  D --> E[Metrics JSON]
  E --> F[Report and monitoring]
```

The pipeline preserves revisions and separates frozen evaluation from post-freeze checks.

`src/` holds analysis and publication code. `dags/` holds interval orchestration. `config/` records the frozen design. `outputs/metrics/` holds versioned evidence. `tests/` exercises contracts. `docs/` explains findings and limits.

### Verification and further reading

The strict JSON replay fails because Prophet metrics differ. All other fields match exactly. Two same-environment repeated fits agree. The cause remains unresolved. All eight seasonal OASIS files validate. Docker operation and hosted CI are unverified. The reviewed literature source is missing.

[Employer PDF](reports/California_Grid_Analytics_Report_Sileshi_Hirpa.pdf) · [Full report](docs/report.md) · [Literature review status](docs/literature_review.md) · [Implementation audit](docs/implementation_audit.md) · [Freeze scope](docs/freeze_scope.md) · [Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)

<details>
<summary>Historical exploratory snapshot</summary>

<!-- baseline:start -->
{baseline}
<!-- baseline:end -->

</details>
'''
    (ROOT/'README.md').write_text(readme)
    # Publication pages are assembled explicitly for predictable employer layout.
    page_text=[('Executive summary',headline+'\n\n'+queue+'\n\n'+event_sentence+'\n\n'+caveat+'\n\nStrict replay remains unverified. The literature source is missing. This report records those limits next to the findings.')]
    page_text += [('Contents','\\tableofcontents')]
    page_text += [('Business questions, data and provenance',sections[0][1].split('\n\n',1)[1]+'\n\n'+sections[2][1])]
    page_text += [sections[i] for i in [3,4,5,6,7,8,9,10]]
    page_text += [('Condensed related work and references','The forecast ladder follows chronological validation and simple baseline comparisons (Hyndman & Athanasopoulos, 2021). Joint contiguous-day resampling addresses dependence in the comparison (Kunsch, 1989). EIA and CAISO documentation motivate source-definition checks. The reviewed source is missing, so the complete literature review remains pending.\n\n'+refs)]
    appendix='''The report builds with `make report`. The demo runs with `make demo`. A fresh clone needs only release dependencies for these saved-metric outputs. Run `python -m src.replay_benchmark --freeze-ref spec-frozen-v1` after restoring the hash-matching archived hourly parquet. Its actual strict comparison outcome must be retained.

Run `python -m src.operator_diagnostics` after restoring saved predictions, the validated OASIS ZIPs and manifest-matching EIA holdout files. Run `python -m src.event_validation .artifacts/benchmark/hourly.parquet` to recompute the retrospective event comparison. These are post-freeze analyses and must not overwrite the published forecast metrics.

G is the geometric mean of authority-level model-to-operator mean daily MAE ratios. MAE and bias are in MW. Bias is forecast minus demand. Coverage counts matched authority-hours and common eligible delivery days. A negative demand shift uses demand from an earlier UTC hour. The upper bound is a one-sided moving-block bootstrap quantile.

The local results notebook reads metric JSON and can optionally inspect archived saved predictions. The historical exploratory notebook is superseded. Raw data, database files, secrets and transient report previews are excluded from version control.

The component inventory records the full source commit for individual file ports. No bundle history was merged into the release branch. The freeze-scope audit records the immutable files and every replay difference. Reference checks are logged separately. No hosted CI result, Docker uptime or live forecast operation is claimed.'''
    page_text += [('Appendix: reproduction and metric definitions',appendix)]
    pdf=[]
    for title,text in page_text:
        text=text.replace('../assets/figures/relative_mae.png','assets/figures/relative_mae.pdf').replace('../assets/figures/ciso_bias.png','assets/figures/ciso_bias.pdf')
        # Keep detailed variants in the web report to fit the PDF results page.
        if title=='Results: post-freeze sensitivity':
            text=text.replace(variants, '\n'.join(variants.splitlines()[:2]+[line for line in variants.splitlines()[2:] if 'shift' in line]))
        if title=='Engineering, monitoring and next steps':
            text+='\n\n![Figure 3. The pipeline preserves revisions and separates evaluation from publication. Source: interval and publication module contracts.](assets/figures/architecture.pdf)'
        if title=='Results: frozen headline':
            text=text.rsplit('\n\n'+queue,1)[0]
        if title=='Results: post-freeze sensitivity':
            short='\n'.join(variants.splitlines()[:2]+[line.replace('adjusted shift','Adjusted hour shift').replace('reported shift','Reported hour shift') for line in variants.splitlines()[2:] if 'shift' in line])
            text=f"{oasis_finding}\n\n{short}\n\nHour shifts are diagnostics. The LDWP-only net-charging proxy is exploratory. Full variant definitions and coverage are in the web report.\n\n![Figure 2. CISO operator bias varies by delivery hour. Source: operator_diagnostics.json.](assets/figures/ciso_bias.pdf)"
        import re
        text=re.sub(r'!\[(.*?)\]\((assets/figures/[^)]+)\)', lambda m:'\\begin{center}\n\\includegraphics[width=4.9in]{'+m.group(2)+'}\n\\end{center}\n\n'+m.group(1),text)
        pdf.append('\\clearpage\n\n'+('\\tableofcontents' if title=='Contents' else '# '+title+'\n\n'+text))
    (ROOT/'reports/report_body.md').write_text('\n\n'.join(pdf)+'\n')
    make_figures()


if __name__=='__main__':generate()
