# Related Work and Benchmarks: A Literature Review for the California Grid Operations Analytics Project

Sileshi Hirpa · November 2026

## Overview

The literature supports the project's three questions, but it answers none of them directly. Load forecasting methods, forecast evaluation statistics and EIA-930 data cleaning are each well developed. No peer-reviewed study was found that tests a locally trained day-ahead model against the balancing authority's own published forecast on EIA-930 under explicit issue-time rules, with dependence-aware inference and a scale-free aggregate across authorities of very different size. No peer-reviewed study was found that traces how EIA demand revisions change a downstream threshold queue. No study was found that validates a weighted grid stress composite against documented CAISO alert days at a fixed review workload.

One candidate gap needs revision. Several open repositories published in 2025 and 2026, none of them peer reviewed, already compare models with EIA-930 operator forecasts. The project's contribution on that question therefore rests on method and on the small California authorities. The comparison itself is no longer new.

- The design rests on established foundations: weather-driven load models (Hong and Fan, 2016), gradient boosting (Ben Taieb and Hyndman, 2014), relative MAE aggregated by geometric mean (Davydenko and Fildes, 2013), Diebold-Mariano tests with the Harvey, Leybourne and Newbold (1997) correction, and block bootstrap inference (Künsch, 1989).
- The gaps are real but narrower than first framed. Open repositories already compare models with operator forecasts, and some report that the operators usually win. RQ1 should be presented as a careful benchmark with strict issue-time rules that covers small authorities, and not as a first attempt.
- The strongest original contributions are RQ2, on how reported versus EIA-adjusted demand changes a peak-normalized review queue, and the event-based validation of the composite stress score. Neither the data-cleaning literature nor the composite-indicator literature tests these downstream operational consequences.

## Introduction and Review Method

This review supports the California Grid Operations Analytics project. The project uses the U.S. Energy Information Administration (EIA) Form EIA-930 Hourly Electric Grid Monitor for five California balancing authorities: CISO (CAISO), BANC, LDWP, IID and TIDC. Their average demand ranges from roughly 280 MW to roughly 24,000 MW. The project asks three questions. RQ1 asks whether a locally trained model improves on each authority's published day-ahead forecast. RQ2 asks which hours an analyst should revisit when EIA revises demand data. A later validation question asks whether a composite stress score captures more documented CAISO alert days than a demand-only rule at equal workload.

The review was conducted in November 2026 as a structured narrative review. It is not a systematic review in the PRISMA sense. Sources were located through publisher pages (ScienceDirect, IEEE, Nature, Taylor and Francis), PubMed Central, arXiv, Semantic Scholar, RePEc, and the websites of EIA, CAISO, CPUC, CEC, NERC, NREL, PNNL and the OECD.

Search terms combined "day-ahead load forecasting," "probabilistic load forecasting," "gradient boosting," "EIA-930," "balancing authority forecast," "data reconciliation," "imputation," "Diebold-Mariano," "block bootstrap," "relative MAE," "composite indicator," "resource adequacy," "heat wave root cause," "hierarchical forecasting" and "graph neural network load."

Methodological works were admitted from 1969 onward. Applied studies were limited to 2010 to 2026. Peer-reviewed journal articles were preferred. Agency reports were admitted as primary sources for operational facts. Open-source repositories and blogs were admitted only where they bear on the gap analysis, and they are labelled as gray literature wherever they appear.

## 1. Short-Term and Day-Ahead Load Forecasting

Load forecasting is one of the oldest applied forecasting problems, and its literature runs to thousands of papers. Hong and Fan (2016), in a tutorial review in the International Journal of Forecasting, group forecasts by horizon into very short, short, medium and long term. They note that most of the literature has concerned point forecasts. Day-ahead forecasting sits within the short-term class. Their review, together with the Global Energy Forecasting Competitions, gives the field its main reference points.

The competitions show what works in practice. GEFCom2012 (Hong, Pinson and Fan, 2014) posed hierarchical load forecasting on Kaggle. Ben Taieb and Hyndman (2014) placed fifth of 105 teams with a separate model for each hour of the day, fitted by component-wise gradient boosting with penalized regression splines. Their main predictors were current and past temperatures and past demand, with calendar effects for time of year, day of week and holidays. GEFCom2014 (Hong, Pinson, Fan, Zareipour, Troccoli and Hyndman, 2016) moved to probabilistic forecasts. GEFCom2017 (Hong, Xie and Black, 2019) added hierarchical probabilistic forecasting. Across these exercises, the winning entries were rarely exotic. Careful feature construction, temperature handling and forecast combination mattered more than model family.

Weather is the dominant driver. Hong, Wang and White (2015) showed that the choice of weather stations alone measurably changes load forecast accuracy. This matters for RQ1 because the balancing authority's own forecast draws on weather forecasts the project cannot see. A local model that used observed next-day temperature would hold an unfair advantage, and one that used no weather at all would be handicapped. A fair comparison uses only weather forecasts available at issue time, or no weather, and states which.

Simple benchmarks remain essential. Hyndman and Athanasopoulos (2021), in Forecasting: Principles and Practice, treat the seasonal naive method as the default baseline for seasonal series. Prophet (Taylor and Letham, 2018) offers a decomposable regression with trend, seasonality and holiday terms, and it is widely used as a reference model. LightGBM (Ke et al., 2017) is a fast gradient-boosted tree implementation that has become standard in tabular forecasting. The M5 competition (Makridakis, Spiliotis and Assimakopoulos, 2022) found that LightGBM-based entries dominated the leading positions on hierarchical retail sales data. The M4 competition (Makridakis, Spiliotis and Assimakopoulos, 2020) found that combinations and hybrids outperformed most pure machine learning entries on 100,000 series, a reminder that model complexity does not guarantee accuracy.

Recent deep learning work on EIA-930 includes an arXiv preprint (arXiv:2602.21415) that benchmarks PowerMamba, S-Mamba, iTransformer, PatchTST and an LSTM on about four years of hourly load from six U.S. ISOs. Such preprints have not been peer reviewed, and they seldom compare against the operator's published forecast. A companion preprint (arXiv:2601.01410) includes a contextual comparison with published CAISO operational forecasts.

**Implication for the project.** The model set of seasonal naive, Prophet and LightGBM with issue-time features is well grounded. The literature gives strong reason to expect that weather information decides much of the outcome. The report should state plainly that a model without issue-time weather forecasts begins at a disadvantage against an operator who has them, and it should interpret a null result for RQ1 in that light.

## 2. Forecast Evaluation Methodology

**Error measures.** Hyndman and Koehler (2006) reviewed accuracy measures. They showed that percentage errors such as MAPE become undefined or unstable when actual values are zero or near zero, and that they penalize over- and under-forecasts unequally. They proposed the mean absolute scaled error (MASE), which scales errors by the in-sample error of a naive method. The project's choice of MAE in megawatts as the primary measure follows this advice directly. Small authorities such as TIDC and IID make the point concrete, since an error of a few megawatts is a large share of a small load.

**Aggregating across series.** Davydenko and Fildes (2013) examined how to summarize accuracy across many series. They showed that the arithmetic mean of relative errors is biased in favour of the benchmark. They recommended the average relative MAE (AvgRelMAE), the geometric mean across series of the ratio of a method's MAE to the benchmark's MAE. In their supply-chain data, judgmental adjustments improved the MAE of statistical forecasts by 10 percent on average under this measure, and MAPE and MASE gave a misleading picture of which adjustments helped. The project's primary statistic is exactly this measure, with the operator forecast as the benchmark. It is scale-free, symmetric in log terms, and unaffected by the difference of two orders of magnitude between CISO and TIDC.

**Comparing predictive accuracy.** Diebold and Mariano (1995) proposed a test of equal accuracy based on the mean loss differential, valid under serial correlation and non-normal errors. Harvey, Leybourne and Newbold (1997) showed that the original test over-rejects in small samples and supplied a corrected statistic that uses Student's t critical values. Giacomini and White (2006) reframed the question as one of conditional predictive ability, which compares forecasting methods, including their estimation windows, rather than population models. This framing suits a shadow trial, where the question is whether the method as deployed would have done better. When five authorities are tested, Holm's (1979) step-down procedure keeps the family-wise error rate at the nominal level with less severity than Bonferroni.

**Dependence-aware resampling.** Hourly forecast errors are strongly autocorrelated within a day and across neighbouring days. Künsch (1989) established the moving-block bootstrap for stationary dependent data, and Politis and Romano (1994) introduced the stationary bootstrap with random block lengths. Resampling whole delivery days in blocks, as the project plans, preserves the error structure within days and the short-range dependence across them. It also yields a confidence interval for the geometric-mean ratio without distributional assumptions.

**Rolling-origin evaluation and leakage.** Tashman (2000) reviewed out-of-sample evaluation and argued for rolling-origin designs that update the forecast origin through the test period. Bergmeir, Hyndman and Koo (2018) showed that standard k-fold cross-validation can be valid for purely autoregressive models with uncorrelated errors, a result that does not extend to features built from future information. Kaufman, Rosset, Perlich and Stitelman (2012) defined leakage as the use of information at training or prediction time that would not be available in deployment, and they showed how it inflates reported accuracy. For a day-ahead benchmark, the likely leaks are actual next-day temperature, lags shorter than the issue-time gap, and demand values revised after issue time. The project's noon Pacific issue-time rule addresses all three.

**Implication for the project.** Each element of the RQ1 statistical plan has a clear precedent: MAE in megawatts, the geometric-mean relative MAE, the block bootstrap over delivery days, Diebold-Mariano tests with the small-sample correction and HAC variance, and Holm adjustment. The literature also suggests reporting MASE, or the ratio to seasonal naive, as a secondary check. Readers can then see whether the operator forecast itself beats a trivial benchmark at each authority.

## 3. Operator Day-Ahead Forecasts as Benchmarks

EIA-930 makes the operator's forecast public. The form's instructions ask each balancing authority for its hourly day-ahead demand forecast alongside actual demand. EIA's 2022 Federal Register notice for the collection states that the data can be used to compare actual demand with the day-ahead forecast as a measure of the forecasting used to commit resources. The same instructions add an important qualification. A balancing authority that does not produce a directly comparable day-ahead forecast in its normal course of business is not required to produce one for EIA. Forecast quality and definition may therefore differ across the five California authorities in ways unrelated to forecasting skill.

The peer-reviewed literature on operator forecast error is older and mostly concerned with reserves. Hodge, Lew and Milligan (2013), in an NREL conference preprint, studied the distributions of day-ahead and two-day-ahead load forecast errors at independent system operators. They found the errors to be non-normal, with implications for how renewable integration studies size reserves. An IEEE paper on a joint seasonal ARMA approach characterized the bias, spread and autocorrelation of day-ahead load forecast errors at several balancing authorities in order to simulate them jointly in planning studies. These studies treat the operator forecast as an input to reliability planning. They do not test whether a public model could do better.

CAISO's own reports show that its day-ahead forecast is one part of a managed process. The Department of Market Monitoring has documented operator adjustments to the load forecast in the residual unit commitment process. From the end of June 2023, CAISO set those adjustments with a quantile regression based on the 97.5th percentile of net load error between day-ahead and real time, and the monitor recommended that the practice be reviewed. The published day-ahead forecast and the quantity actually used to commit resources can therefore differ. A benchmark against the published value measures only the former.

The most direct comparisons now come from gray literature. Several open repositories published in 2025 and 2026 score models against EIA-930 operator forecasts, with mixed findings. One reports that across 17 balancing authorities the operator forecasts beat a LightGBM model from 2021 to 2026 (MAPE of 3.75 percent against 4.99 percent). Another reports that a LightGBM model lost to MISO's published forecast over a twelve-month walk-forward test. A third reports that a fine-tuned foundation model beat operator submissions at six of seven RTOs. An independent audit reports that EIA-930's CISO demand series has carried hour labels shifted by one hour relative to CAISO's own OASIS data since 14 June 2022, while the CISO forecast column matches CAISO's forecast exactly. None of these claims has been peer reviewed, and they should be treated as leads to verify. They are nonetheless highly relevant, because a one-hour misalignment would inflate CISO's apparent operator error and bias RQ1 toward the local model.

**Implication for the project.** RQ1 is less novel than first supposed, and its value lies in rigour and coverage. The project should verify CISO hour alignment against CAISO OASIS before scoring, report the operator forecast's skill against seasonal naive for each authority, and state that the published day-ahead forecast is not necessarily the quantity used for unit commitment.

## 4. EIA-930 Data Quality, Revisions and Anomaly Handling

EIA states that EIA-930 data are collected as reported from balancing authorities through automated processes and published in near real time, which can produce anomalous values. EIA works with respondents to correct anomalies in the historical record. The data are therefore revised in place, and a later download can differ from an earlier one for the same hour. Demand in EIA-930 is a derived quantity. Each authority computes it as metered net generation minus metered total interchange, so an error in either input passes into demand.

Ruggles, Farnham, Tong and Caldeira (2020), in Scientific Data, produced the standard reference on cleaning these data. Working with 56 balancing authorities, they found that 2.2 percent of hourly demand values were missing in data queried on 10 September 2019. Their screening flagged anomalous values that made up about 0.5 percent of the data, including blanks, zeros, negatives, spikes and implausible runs. They imputed missing and flagged values with Multiple Imputation by Chained Equations (MICE). Cross-validation gave a mean absolute percentage error of 3.5 percent and a mean bias of 0.33 percent across authorities. They also described EIA's own rule. EIA flags an hourly value as anomalous if it is missing, negative, zero, or at least 1.5 times the authority's previously reported maximum, and it replaces the value from neighbouring hours and days. At that time EIA applied the rule only when building regional totals and left authority-level data as reported.

De Chalendar and Benson (2021), in Applied Energy, took a physical approach. They modelled the grid as a graph of balancing areas linked by transmission and solved an optimization that makes the smallest adjustments needed to satisfy energy conservation across demand, generation and interchange. Their reconciled dataset covers 68 balancing areas and is updated hourly. It builds on the emissions tracking framework of de Chalendar, Taggart and Benson (2019) in PNAS. The Public Utility Data Liberation project (PUDL) of Catalyst Cooperative integrated EIA-930 in 2024 and later added an imputed version of authority-level demand. A public issue in the PUDL repository notes that those imputed values differed slightly between builds from identical inputs, which shows that even careful imputation pipelines can be hard to reproduce exactly.

EIA now publishes adjusted and imputed demand alongside reported demand. Every user therefore chooses a target series, but the literature offers little guidance on how the choice affects analysis built on top of it. The project's own example is instructive. At BANC, a reported hour of 9,770 MW was revised to 2,296 MW. Because the stress index divides each hour by the authority's peak, a single spike of this size lowers every other hour's share of peak and can empty the review queue. Peak-normalized rules are unusually sensitive to one bad value, since that value sits in the denominator of every hour.

A further issue is publication vintage. EIA does not distribute archived vintages, so a study cannot know what an analyst would have seen at issue time. The September 2022 heat wave shows the same problem outside EIA. CAISO publicly reported a record instantaneous peak of 52,061 MW on 6 September 2022, while the CPUC's Public Advocates Office observed that CAISO's own reported data showed 51,426 MW. Two authoritative figures for the same quantity can coexist.

**Implication for the project.** RQ2 occupies a space between two literatures. The cleaning studies ask how to produce a plausible series, and the forecasting studies take a cleaned series as given. Neither asks which operational decisions change when the series changes. The project should report queue membership under reported and adjusted demand, count the hours that enter or leave the queue, and separate changes caused by revised peaks from changes caused by revised individual hours. It should also check the energy balance identity hour by hour and handle daylight-saving transitions in UTC.

## 5. Grid Stress, Resource Adequacy and Event Detection

Formal adequacy assessment rests on probabilistic measures such as loss of load expectation and on planning reserve margins, as used in NERC's reliability assessments. NERC's 2025 Long-Term Reliability Assessment, released on 29 January 2026, forecasts summer peak demand growth of 224 GW and winter peak growth of 246 GW over its ten-year horizon. Most of the projected increase comes from new data centres. These measures require generator availability data and probabilistic simulation, which EIA-930 does not provide. The project's stress index is therefore an operational indicator of load relative to an authority's own history. It should not be presented as an adequacy metric.

California's stress has a characteristic timing. Denholm, O'Connell, Brinkman and Jorgenson (2015), in an NREL technical report, explained the "duck chart," in which solar output depresses midday net load and steepens the evening ramp. The joint Final Root Cause Analysis by CAISO, the CPUC and the CEC, issued on 13 January 2021, found no single cause for the rotating outages of 14 and 15 August 2020. It identified three factors. A heat wave across the West pushed demand beyond resource adequacy and planning targets. Those targets did not provide enough resources for the early evening hours of extremely hot days. Market practices, including under-scheduling of load in the day-ahead market, worsened conditions under stress.

The September 2022 heat wave produced CAISO's record peak of 52,061 MW at 4:58 p.m. on 6 September. CAISO's Summer Market Performance Report for September 2022 states that this load far exceeded the 49,748 MW of resource adequacy capacity shown to the ISO and was 7,483 MW above the CEC forecast. Flex Alerts ran for a record ten consecutive days, and no rotating outages occurred.

These reports teach two lessons for a stress index. First, the binding hours fell in the early evening, when net load peaks, and not always at the gross peak. Second, imports mattered. The 2020 analysis stresses the West-wide reach of the heat, which limited imports when they were most needed. Both lessons support the composite's inclusion of import reliance alongside demand.

Composite indices carry their own literature. The OECD and European Commission Joint Research Centre Handbook on Constructing Composite Indicators (Nardo, Saisana, Saltelli and Tarantola, 2008) sets out a ten-step process. It warns that with linear aggregation, weights act as trade-offs between components and not as measures of importance. It also recommends uncertainty and sensitivity analysis on the weights and validation against related measurable events. The project's weights of 0.50, 0.30 and 0.20 are judgmental, which the handbook regards as acceptable only when tested. Validation against documented alert days is the external check the handbook calls for.

Event detection at a fixed workload is best framed with precision and recall. Saito and Rehmsmeier (2015) showed that precision-recall curves are more informative than ROC curves when positive cases are rare, as alert days are. Comparing two rules on the same days calls for a paired test. McNemar's test is the standard choice, and Fagerland, Lydersen and Laake (2013) found that its mid-p version performs better than the exact conditional version in small samples. Fixing K, the number of days flagged, holds analyst workload constant and guards against alert fatigue, the tendency of operators to discount frequent alarms.

**Implication for the project.** The validation design is sound. The project should report precision and recall at several values of K, apply the mid-p McNemar test alongside the exact test, and run a weight sensitivity analysis in the manner of the OECD and JRC handbook. CAISO's Grid Emergencies History Report is the natural source for labelling alert days, and the labels should be fixed before any score is computed.

## 6. Spatial and Cross-Region Dependence

Hierarchical forecasting offers a principled way to use related series. Hyndman, Ahmed, Athanasopoulos and Shang (2011) proposed optimal combination of forecasts across a hierarchy, and Wickramasuriya, Athanasopoulos and Hyndman (2019) developed the minimum-trace (MinT) reconciliation method. GEFCom2012 and GEFCom2017 both posed hierarchical load problems. Graph neural networks have been applied to multi-area load forecasting with reported gains, though much of this work concerns photovoltaic output or synthetic graphs. One 2025 arXiv study found that graph models gained most over non-graph baselines when spatial correlation was introduced artificially, which suggests that gains on real regional load may be modest.

Granger causality (Granger, 1969) tests whether past values of one series improve prediction of another. With strongly seasonal, trending series that share a common weather driver, Granger tests readily detect "causality" that reflects shared temperature and calendar patterns. High pairwise correlation among the California authorities is expected for the same reason.

**Implication for the project.** The earlier finding, that cross-authority features did not improve forecasts despite strong correlation and Granger results, is consistent with this literature. It justifies the decision not to build a graph neural network. The appendix should describe Granger results as predictive association conditional on the chosen lags, and not as evidence of physical influence.

## 7. Reproducible Pipelines and Forecasting Practice

Hong, Pinson, Wang, Weron, Yang and Zareipour (2020), in their review of energy forecasting, call for open data, reproducible benchmarks and honest comparison with simple methods. The M4 and M5 competitions made code submission and replication standard practice in forecasting research. In energy data, the PUDL reproducibility issue noted above shows that randomized imputation can break exact replication even with fixed inputs. The main risks are silent revision of the target series, accidental use of future data, and inability to reconstruct what a model saw on a given day. Orchestration tools such as Apache Airflow, versioned raw snapshots, and stored forecasts with their issue timestamps address each of them.

**Implication for the project.** Because EIA revises data in place, the pipeline should save dated raw snapshots from now on, so that future evaluations can use true vintages. Historical evaluations should be labelled as retrospective.

## Summary of Key Studies

The table lists the sources that carry the most weight in the design, grouped by the question they inform. Gray literature is marked as such.

| Study | Type | Contribution | Informs |
| --- | --- | --- | --- |
| Hong and Fan (2016) | Peer-reviewed review | Probabilistic load forecasting, horizons and scoring | RQ1 framing |
| Hong, Pinson and Fan (2014) | Peer-reviewed | GEFCom2012 hierarchical load competition | RQ1 |
| Hong et al. (2016) | Peer-reviewed | GEFCom2014 probabilistic competition | RQ1 |
| Ben Taieb and Hyndman (2014) | Peer-reviewed | Gradient boosting per hour, fifth of 105 teams | RQ1 model choice |
| Hong, Wang and White (2015) | Peer-reviewed | Weather station choice changes accuracy | RQ1 weather rules |
| Ke et al. (2017) | Peer-reviewed (NeurIPS) | LightGBM | RQ1 model |
| Taylor and Letham (2018) | Peer-reviewed | Prophet | RQ1 model |
| Makridakis et al. (2020, 2022) | Peer-reviewed | M4 and M5 competitions | RQ1 benchmarks |
| Hyndman and Koehler (2006) | Peer-reviewed | MASE and the pitfalls of MAPE | RQ1 metric |
| Davydenko and Fildes (2013) | Peer-reviewed | Geometric-mean relative MAE | RQ1 primary statistic |
| Diebold and Mariano (1995) | Peer-reviewed | Test of equal predictive accuracy | RQ1 inference |
| Harvey, Leybourne and Newbold (1997) | Peer-reviewed | Small-sample correction to DM test | RQ1 inference |
| Giacomini and White (2006) | Peer-reviewed | Conditional predictive ability | RQ1 shadow trial |
| Künsch (1989) | Peer-reviewed | Moving-block bootstrap | RQ1 intervals |
| Hodge, Lew and Milligan (2013) | NREL conference preprint | Operator forecast error distributions | RQ1 operator benchmark |
| Ruggles et al. (2020) | Peer-reviewed | EIA-930 screening and MICE imputation, 56 BAs | RQ2 |
| de Chalendar and Benson (2021) | Peer-reviewed | Physics-based reconciliation, 68 areas | RQ2, energy balance |
| CAISO, CPUC and CEC (2021) | Agency report | August 2020 root cause analysis | Validation labels |
| CAISO (2022) | Agency report | September 2022 heat wave performance | Validation labels |
| Nardo et al. (2008) | OECD and JRC handbook | Building and testing composite indicators | Composite weights |
| Saito and Rehmsmeier (2015) | Peer-reviewed | Precision-recall for rare events | Validation metric |
| Fagerland, Lydersen and Laake (2013) | Peer-reviewed | McNemar test variants in small samples | Validation test |
| Hyndman et al. (2011), Wickramasuriya et al. (2019) | Peer-reviewed | Hierarchical forecast reconciliation | Spatial appendix |
| Open EIA-930 repositories (2025 to 2026) | Gray literature | Models versus operator forecasts, mostly MAPE | RQ1 gap revision |

## Literature Gap and Contribution

Each candidate gap was tested against the evidence gathered above. Three are confirmed and one is narrowed.

**Gap 1, benchmarks against the operator's forecast, is partly filled and must be restated.** The review found no peer-reviewed study of this kind for EIA-930. Operator forecast errors have been studied as reserve inputs (Hodge, Lew and Milligan, 2013), and academic models are routinely compared with each other, but not with the operator. The gray literature, however, now contains several open comparisons with conflicting results. These projects mostly use MAPE, favour large authorities, rarely state the operator's issue time, and seldom report intervals that account for dependence. The refined gap is methodological and specific to a population. No known study combines strict issue-time information rules, the geometric-mean relative MAE of Davydenko and Fildes (2013), block bootstrap intervals over delivery days, and corrected Diebold-Mariano tests across authorities that differ in scale by two orders of magnitude, including very small ones.

**Gap 2, revisions and downstream analytics, is confirmed.** Ruggles et al. (2020) and de Chalendar and Benson (2021) show how to produce plausible or physically consistent series. Forecasting studies choose a target series and proceed. No study found asks how the choice between reported and adjusted demand alters an operational product such as a peak-normalized review queue. The BANC example shows that the effect can be large, because a single revised spike changes the denominator for every hour.

**Gap 3, validation of composite stress indices, is confirmed with a qualification.** The OECD and JRC handbook prescribes sensitivity analysis and external validation, and agency reports document stress events in detail. No study was found that validates a judgmentally weighted grid stress composite against documented CAISO alert days at a fixed review workload with a paired test. The qualification is that the alert record is short and dominated by a few heat waves, so any validation will have limited statistical power.

**Gap 4, the small California authorities, is confirmed.** BANC, LDWP, IID and TIDC appear in national datasets such as those of Ruggles et al. (2020) and de Chalendar and Benson (2021). No study was found that examines their forecast accuracy or data quality individually. Their small loads magnify both percentage errors and the effect of single bad values.

The project's contribution is accordingly modest and specific.

- **RQ1:** a dependence-aware benchmark of simple local models against published day-ahead forecasts for five California authorities, under strict issue-time rules and summarized by a scale-free statistic.
- **RQ2:** a documented account of how EIA revisions change membership of a threshold-based review queue.
- **Validation:** a test of whether a weighted composite captures more documented alert days than a demand-only rule at equal workload.

The project does not make causal claims. Granger results and composite scores describe association. Where publication vintages are unavailable, the evaluation is a retrospective simulation on data as currently published, which may contain corrections unavailable at issue time. The stress index is not a resource adequacy, reserve margin or loss-of-load assessment, and it should not be read as a measure of reliability risk.

In the four sampled weeks, a one-hour shift narrowed the CISO daylight-time discrepancies. December aligned best without a shift. Matching the operator’s time convention therefore matters when interpreting forecast rankings.

## Implications for Methodology

1. Verify CISO hour alignment against CAISO OASIS before scoring, and document how each authority's forecast is defined and issued.
2. Keep MAE in megawatts as the primary measure and the geometric-mean relative MAE with block bootstrap intervals as the primary statistic. Add each authority's ratio to seasonal naive as context.
3. Use the Harvey, Leybourne and Newbold correction and Holm adjustment for any Diebold-Mariano tests.
4. Run RQ2 under both reported and adjusted demand, and separate queue changes caused by revised peaks from those caused by revised hours.
5. Fix alert-day labels in advance, report precision and recall at several values of K, and test sensitivity to the composite weights.
6. Save dated raw snapshots from now on, so that future work can use true vintages.

## Caveats

Several sources used here are agency reports or gray literature. The open EIA-930 repositories are cited only to show the state of practice, and their numerical claims, including the CISO hour shift, are unverified. The NREL work by Hodge, Lew and Milligan is a conference preprint. The graph neural network evidence draws partly on arXiv preprints. Two figures exist for CAISO's September 2022 peak (52,061 MW and 51,426 MW), and the report should state which source it uses.

## References

Ben Taieb, S., & Hyndman, R. J. (2014). A gradient boosting approach to the Kaggle load forecasting competition. *International Journal of Forecasting, 30*(2), 382-394. https://doi.org/10.1016/j.ijforecast.2013.07.005

Diebold, F. X., & Mariano, R. S. (1995). Comparing Predictive Accuracy. *Journal of Business &amp; Economic Statistics, 13*(3), 253-263. https://doi.org/10.1080/07350015.1995.10524599

Granger, C. W. J. (1969). Investigating Causal Relations by Econometric Models and Cross-spectral Methods. *Econometrica, 37*(3), 424. https://doi.org/10.2307/1912791

Hong, T., Pinson, P., & Fan, S. (2014). Global Energy Forecasting Competition 2012. *International Journal of Forecasting, 30*(2), 357-363. https://doi.org/10.1016/j.ijforecast.2013.07.001

Hong, T., Pinson, P., Fan, S., Zareipour, H., Troccoli, A., & Hyndman, R. J. (2016). Probabilistic energy forecasting: Global Energy Forecasting Competition 2014 and beyond. *International Journal of Forecasting, 32*(3), 896-913. https://doi.org/10.1016/j.ijforecast.2016.02.001

Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting, 22*(4), 679-688. https://doi.org/10.1016/j.ijforecast.2006.03.001

Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61 forecasting methods. *International Journal of Forecasting, 36*(1), 54-74. https://doi.org/10.1016/j.ijforecast.2019.04.014

Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). M5 accuracy competition: Results, findings, and conclusions. *International Journal of Forecasting, 38*(4), 1346-1364. https://doi.org/10.1016/j.ijforecast.2021.11.013

Saito, T., & Rehmsmeier, M. (2015). The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets. *PLOS ONE, 10*(3), e0118432. https://doi.org/10.1371/journal.pone.0118432

Wickramasuriya, S. L., Athanasopoulos, G., & Hyndman, R. J. (2019). Optimal Forecast Reconciliation for Hierarchical and Grouped Time Series Through Trace Minimization. *Journal of the American Statistical Association, 114*(526), 804-819. https://doi.org/10.1080/01621459.2018.1448825
