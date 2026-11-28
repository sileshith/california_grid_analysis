# Post-freeze operator definition checks

The seasonal evidence supports retaining demand-definition and alignment caveats. CISO operator forecasts closely match OASIS DAM, while actual demand definitions differ. LDWP model ranking reverses when the sampled EIA target is replaced with OASIS actuals. No full-window superiority claim follows.

## Local hour, month and shift checks

Bias is operator forecast minus target demand. At time t, the shift compares the forecast with demand at t plus the stated shift. The saved forecasts are unchanged. Every authority, both demand versions, all local hours and months are recorded in the [diagnostic JSON](../outputs/metrics/operator_diagnostics.json).

| Authority | Demand version | Shift (h) | Matched hours | Bias (MW) | MAE (MW) |
| --- | --- | ---: | ---: | ---: | ---: |
| CISO | adjusted | -1 | 6358 | -1,773.49 | 2,590.15 |
| LDWP | adjusted | -1 | 6358 | -264.56 | 311.37 |
| CISO | adjusted | 0 | 6359 | -1,773.45 | 2,160.58 |
| LDWP | adjusted | 0 | 6359 | -264.70 | 304.74 |
| CISO | adjusted | 1 | 6358 | -1,773.84 | 1,966.48 |
| LDWP | adjusted | 1 | 6358 | -264.77 | 322.54 |
| CISO | reported | -1 | 6335 | -1,779.95 | 2,595.84 |
| LDWP | reported | -1 | 6358 | -264.56 | 311.37 |
| CISO | reported | 0 | 6335 | -1,780.16 | 2,168.76 |
| LDWP | reported | 0 | 6359 | -264.70 | 304.74 |
| CISO | reported | 1 | 6334 | -1,780.76 | 1,970.00 |
| LDWP | reported | 1 | 6358 | -264.77 | 322.54 |

## Seasonal OASIS comparisons

Every accepted file contains the expected report item and market, unique complete CAISO hourly coverage, valid timestamps and numeric MW. The two April files were kept. Remaining requests were sequential and spaced by at least the required interval. The [request manifest](../verification/oasis_download_requests.json) records exact URLs, targets, attempts and file hashes.

| Authority | Market | EIA field | Week start UTC | Hours | Mean absolute difference (MW) | Bias, EIA minus OASIS (MW) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| CISO | DAM | authority | 20250407T07:00-0000 | 168 | 0.240 | 0.013 |
| LDWP | DAM | authority | 20250407T07:00-0000 | 168 | 10.014 | -7.214 |
| CISO | ACTUAL | actual | 20250407T07:00-0000 | 168 | 824.649 | -101.387 |
| CISO | ACTUAL | reported | 20250407T07:00-0000 | 168 | 824.649 | -101.387 |
| LDWP | ACTUAL | actual | 20250407T07:00-0000 | 168 | 366.446 | 366.446 |
| LDWP | ACTUAL | reported | 20250407T07:00-0000 | 168 | 366.446 | 366.446 |
| CISO | DAM | authority | 20250707T07:00-0000 | 168 | 0.263 | -0.032 |
| LDWP | DAM | authority | 20250707T07:00-0000 | 168 | 41.589 | 6.996 |
| CISO | ACTUAL | actual | 20250707T07:00-0000 | 168 | 1,192.036 | -164.345 |
| CISO | ACTUAL | reported | 20250707T07:00-0000 | 168 | 1,192.036 | -164.345 |
| LDWP | ACTUAL | actual | 20250707T07:00-0000 | 168 | 378.988 | -50.095 |
| LDWP | ACTUAL | reported | 20250707T07:00-0000 | 168 | 378.988 | -50.095 |
| CISO | DAM | authority | 20251006T07:00-0000 | 168 | 0.240 | 0.029 |
| LDWP | DAM | authority | 20251006T07:00-0000 | 168 | 59.163 | -33.812 |
| CISO | ACTUAL | actual | 20251006T07:00-0000 | 168 | 823.762 | -49.583 |
| CISO | ACTUAL | reported | 20251006T07:00-0000 | 168 | 823.762 | -49.583 |
| LDWP | ACTUAL | actual | 20251006T07:00-0000 | 168 | 141.113 | 112.137 |
| LDWP | ACTUAL | reported | 20251006T07:00-0000 | 168 | 141.113 | 112.137 |
| CISO | DAM | authority | 20251201T08:00-0000 | 168 | 0.257 | 0.019 |
| LDWP | DAM | authority | 20251201T08:00-0000 | 168 | 29.658 | 13.467 |
| CISO | ACTUAL | actual | 20251201T08:00-0000 | 168 | 241.268 | -91.994 |
| CISO | ACTUAL | reported | 20251201T08:00-0000 | 168 | 241.268 | -91.994 |
| LDWP | ACTUAL | actual | 20251201T08:00-0000 | 168 | 398.321 | 398.321 |
| LDWP | ACTUAL | reported | 20251201T08:00-0000 | 168 | 398.321 | 398.321 |

## Alignment against OASIS actuals

| Authority | Week start UTC | EIA target shift (h) | Hours | Mean absolute difference (MW) |
| --- | --- | ---: | ---: | ---: |
| CISO | 20250407T07:00-0000 | -1 | 168 | 1,485.488 |
| CISO | 20250407T07:00-0000 | 0 | 168 | 824.649 |
| CISO | 20250407T07:00-0000 | 1 | 168 | 102.964 |
| LDWP | 20250407T07:00-0000 | -1 | 168 | 367.536 |
| LDWP | 20250407T07:00-0000 | 0 | 168 | 366.446 |
| LDWP | 20250407T07:00-0000 | 1 | 168 | 366.042 |
| CISO | 20250707T07:00-0000 | -1 | 168 | 2,234.815 |
| CISO | 20250707T07:00-0000 | 0 | 168 | 1,192.036 |
| CISO | 20250707T07:00-0000 | 1 | 168 | 152.345 |
| LDWP | 20250707T07:00-0000 | -1 | 168 | 383.280 |
| LDWP | 20250707T07:00-0000 | 0 | 168 | 378.988 |
| LDWP | 20250707T07:00-0000 | 1 | 168 | 399.726 |
| CISO | 20251006T07:00-0000 | -1 | 168 | 1,517.012 |
| CISO | 20251006T07:00-0000 | 0 | 168 | 823.762 |
| CISO | 20251006T07:00-0000 | 1 | 168 | 66.655 |
| LDWP | 20251006T07:00-0000 | -1 | 168 | 164.065 |
| LDWP | 20251006T07:00-0000 | 0 | 168 | 141.113 |
| LDWP | 20251006T07:00-0000 | 1 | 168 | 189.786 |
| CISO | 20251201T08:00-0000 | -1 | 168 | 947.899 |
| CISO | 20251201T08:00-0000 | 0 | 168 | 241.268 |
| CISO | 20251201T08:00-0000 | 1 | 168 | 619.929 |
| LDWP | 20251201T08:00-0000 | -1 | 168 | 398.393 |
| LDWP | 20251201T08:00-0000 | 0 | 168 | 398.321 |
| LDWP | 20251201T08:00-0000 | 1 | 168 | 398.196 |

CISO agreement improves with the following EIA hour in the spring, summer and autumn samples, but not in winter. This supports an alignment concern and contradicts a single uniform shift as a complete explanation. The sample does not identify the correct publication convention. LDWP discrepancies persist across shifts. No physical storage cause is established.

## Storage fields and supported proxy

Exact bulk header names follow. They are preserved verbatim, including source spelling. The holdout files match the frozen source digests.

### EIA930_BALANCE_2025_Jan_Jun.csv

- `Net Generation (MW) from Hydropower Excluding Pumped Storage`
- `Net Generation (MW) from Pumped Storage`
- `Net Generation (MW) from Solar without Integrated Battery Storage`
- `Net Generation (MW) from Solar with Integrated Battery Storage`
- `Net Generation (MW) from Wind without Integrated Battery Storage`
- `Net Generation (MW) from Wind with Integrated Battery Storage`
- `Net Generation (MW) from Battery Storage`
- `Net Generation (MW) from Other Energy Storage`
- `Net Generation (MW) from Unknown Energy Storage`
- `Net Generation (MW) from Hydropower Excluding Pumped Storage (Imputed)`
- `Net Generation (MW) from Pumped Storage (Imputed)`
- `Net Generation (MW) from Solar without Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Solar with Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Wind without Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Wind with Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Battery Storage (Imputed)`
- `Net Generation (MW) from Other Energy Storage (Imputed)`
- `Net Generation (MW) from Unknown Energy Storage (Imputed)`
- `Net Generation (MW) from Hydropower Excluding Pumped Storage (Adjusted)`
- `Net Generation (MW) from Pumped Storage  (Adjusted)`
- `Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Wind without Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Wind with Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Battery Storage (Adjusted)`
- `Net Generation (MW) from Other Energy Storage (Adjusted)`
- `Net Generation (MW) from Unknown Energy Storage (Adjusted)`

### EIA930_BALANCE_2025_Jul_Dec.csv

- `Net Generation (MW) from Hydropower Excluding Pumped Storage`
- `Net Generation (MW) from Pumped Storage`
- `Net Generation (MW) from Solar without Integrated Battery Storage`
- `Net Generation (MW) from Solar with Integrated Battery Storage`
- `Net Generation (MW) from Wind without Integrated Battery Storage`
- `Net Generation (MW) from Wind with Integrated Battery Storage`
- `Net Generation (MW) from Battery Storage`
- `Net Generation (MW) from Other Energy Storage`
- `Net Generation (MW) from Unknown Energy Storage`
- `Net Generation (MW) from Hydropower Excluding Pumped Storage (Imputed)`
- `Net Generation (MW) from Pumped Storage (Imputed)`
- `Net Generation (MW) from Solar without Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Solar with Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Wind without Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Wind with Integrated Battery Storage (Imputed)`
- `Net Generation (MW) from Battery Storage (Imputed)`
- `Net Generation (MW) from Other Energy Storage (Imputed)`
- `Net Generation (MW) from Unknown Energy Storage (Imputed)`
- `Net Generation (MW) from Hydropower Excluding Pumped Storage (Adjusted)`
- `Net Generation (MW) from Pumped Storage  (Adjusted)`
- `Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Wind without Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Wind with Integrated Battery Storage (Adjusted)`
- `Net Generation (MW) from Battery Storage (Adjusted)`
- `Net Generation (MW) from Other Energy Storage (Adjusted)`
- `Net Generation (MW) from Unknown Energy Storage (Adjusted)`

Observed dedicated battery-generation values in the saved holdout support: BANC: 0, CISO: 0, IID: 6553, LDWP: 6592, TIDC: 0.

CISO has no observed dedicated battery values, so the dedicated net-generation field cannot supply a CISO correction. The supported exploratory proxy changes LDWP only. Its formula is LDWP adjusted demand plus the minimum of battery net generation and zero. Other authorities retain their original targets. Missing LDWP values remain unavailable. Integrated, pumped and other storage are not removed. Net fleet generation cannot reveal simultaneous gross charging and discharge.

## Rescoring fixed predictions

| Variant | G | One-sided upper bound | Common days |
| --- | ---: | ---: | ---: |
| adjusted_shift_-1 | 1.168557 | 1.216186 | 265 |
| adjusted_shift_+0 | 1.470674 | 1.571009 | 265 |
| adjusted_shift_+1 | 1.204707 | 1.256138 | 265 |
| reported_shift_-1 | 1.164315 | 1.209661 | 263 |
| reported_shift_+0 | 1.455315 | 1.544241 | 263 |
| reported_shift_+1 | 1.199912 | 1.246865 | 263 |
| seasonal_original_adjusted | 1.365470 | 1.718644 | 27 |
| seasonal_oasis_actual | 1.987986 | 2.479404 | 27 |
| seasonal_oasis_actual_and_operator | 2.024761 | 2.538876 | 27 |
| adjusted_ldwp_net_battery_charging_proxy | 1.468697 | 1.560083 | 264 |

Seasonal variants share the sampled-week baseline. They cannot be interpreted as full-window estimates. Their per-authority ratios and coverage are saved in [forecast_sensitivity.json](../outputs/metrics/forecast_sensitivity.json). Shifted targets also change the loss comparison itself, so a lower G does not validate a clock convention. The frozen headline remains unchanged.
