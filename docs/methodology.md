# Scientific methodology

## Units and labels

The source contains 3,827 observations, 383 with >=0.1% indels. Reproduction identity is guide sequence + off-target sequence + chromosome. Of 1,882 identities, 76 have discordant labels. Excluding them leaves 1,806 sites, 118 positives and 26 guides. Filtering both sequences to 23 nt gives 1,768 sites and 114 positives. Length is a compatibility proxy, not proof that no compensating bulges exist.

Measured negatives are below-threshold outcomes, not proof of zero cleavage. Negative delta-indel measurements remain valid background-corrected observations. Unmeasured candidates and observations excluded for conflict remain unlabeled in this cohort. Neither becomes a measured negative.

## Estimands

- AUROC describes discrimination between measured positive and negative sites.
- Average precision uses precision weighted by recall increments at tied score thresholds. Trapezoidal AUPRC linearly interpolates PR coordinates. Both are exported explicitly.
- Classification uses only measured scored sites. Each-model and common-scored cohorts are reported. The common subset controls comparability but may select an easier cohort, so coverage accompanies it.
- Candidate coverage = scored measured sites / all measured sites in scope. Positive coverage = scored positives / all positives. These are not genome-wide sensitivity.
- Recall@K retains original per-guide ranks and includes unscored positives in the denominator. Macro recall averages eligible guides equally. Micro recall pools hits and positives. Four guides without positives are excluded from macro recall. Tied ranks can select more than K sites and are flagged.
- Exact-budget recall takes at most K identities. For a boundary tie of n candidates containing p known positives, choosing m contributes m*p/n expected hits under uniform tie ordering. Worst/best counts are max(0,m-(n-p)) and min(m,p). These are ordering bounds, not confidence intervals. Unknown sites affect budget, not classification labels.

## Undefined statistics

Empty and single-class cohorts return null discrimination metrics with reason codes. AP would equal one for an all-positive sample but has no negative-class discrimination, so this release intentionally suppresses it. Precision is undefined when nothing is selected. Recall is undefined when no positives exist. JSON uses null, never NaN/Infinity.

## Uncertainty

Fix the common cohort before sampling. AP intervals use 1,000 percentile resamples, seed 20261019. The row baseline treats observations independently; the guide alternative preserves within-guide dependence. Repeatedly sampled guides contribute repeated rows. Record valid resample counts. Intervals condition on this dataset and omit assay limits, model-training uncertainty and transportability.

Paired macro recall differences resample the same positive-bearing guides for both models, 2,000 times. Results are exploratory, without multiplicity correction. Label sensitivity uses 0.01%, 0.05%, 0.1%, 0.5% and 1.0%, rebuilding conflict exclusions and shared cohorts each time. Score cutoffs are descriptive; no deployment threshold is selected.

## Reproduction boundary

Metrics are independently recomputed from existing predictions. No models, genomes or wet-lab measurements are regenerated. Four models match 20 stored recall cells. CCTop's five cells remain discrepant. Deposited coarse ties violate a literal K-candidate budget.

The upstream PR implementation sorts matched sites by per-guide rank and divides by all truth positives, including unscored positives. That differs from standard score-threshold AP conditional on the scored cohort. BioG names its estimands instead of adjusting them to match a headline result.
