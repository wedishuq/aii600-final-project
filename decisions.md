# Decisions

This file is the history of the project. Append an entry when a choice changes the work: the quantity, the data, the split, the model, the loss, or the action. Leave old entries in place. A later entry can reverse an earlier one. If a result depends on a random draw, record the seed under Why. The split entry records the cutoff date, or the seed and the fraction. The pull request that merges the code names this entry.

## 2026-11-11: Use Antivirus Detection Data

- **Decision.** Use antivirus detection events and historical endpoint activity to predict the probability that an alert is malicious using logistic regression.
- **Why.** Antivirus telemetry provides detection classifications and behavioral context for evaluating malicious activity. The model will use log loss and a cost-based escalation threshold.
- **Alternative.** Use broader endpoint security events or the CERT insider-threat dataset.
- **Revisit.** If reliable malicious/benign labels are unavailable or the antivirus data is insufficient for training and evaluation.

## 2026-11-16: Proposal stands

- Decision. The proposal stands. Use the organization's endpoint-security alert logs if approval is in hand, and the CERT Insider Threat Test Dataset otherwise. Keep the role-fit score as an input. A person makes the escalate-or-close call. The quantity is the probability that one alert is malicious rather than a false positive.
- Why. The professor said the proposal can proceed as written, including the organization-or-CERT choice, the role-fit score, and the limit that a person makes the call.
- Alternative. Dropping role fit and treating the file-detection field lists as the dataset. Those files name fields that appeared at least once. They are not the alerts, and they have no job role and no analyst verdict.
- Revisit. If approval is refused, the data line becomes CERT. If a labelled export arrives, record its source, unit, and time span in `data/README.md`.

## 2026-11-16: Logistic probability, cost cutoff, cost score

- Decision. Fit $P(\text{malicious}\mid\text{alert})$ by logistic regression, minimizing log loss. Escalating a false positive costs $C_{FP}$. Closing a real attack costs $C_{MISS}$. A correct call costs nothing. Escalate when the expected cost of escalating is lower:

  $$
  (1-p)\,C_{FP} < p\,C_{MISS},
  $$

  which is the cutoff

  $$
  p > \frac{C_{FP}}{C_{FP}+C_{MISS}}.
  $$

  On the held-out period, score the mean cost per alert under that rule against the mean cost of closing every alert. The dollar or hour amounts of $C_{FP}$ and $C_{MISS}$ are not set yet.
- Why. This is the week 7 rule. In the German-credit example the two costs, $0.25$ and $1$, put the cutoff at $1/5$ rather than $1/2$, and lending to everyone was right on 70% of loans while losing money. The model supplies $p$. The costs supply the cutoff. The professor named closing every alert as the comparison.
- Alternative. Accuracy, F1, or a classifier that only ranks alerts. Those treat the two mistakes as the same, or they never produce a probability the cost rule can use. An L2 penalty, as in Lab 7 section 2.6, is not part of this entry. Plain log loss is the fit.
- Revisit. If the held-out probabilities are not calibrated, the cutoff is the wrong place to cut even when the costs are right. If a coefficient diverges because malicious alerts are rare, then consider the penalty, and record that as a new entry. Set $C_{FP}$ and $C_{MISS}$ before scoring, and check the score again with $C_{MISS}$ halved and doubled.

## 2026-11-16: Stand-in label from the allow-list (three-way)

- Decision. The stand-in label comes from the product status list, keyed on `prod_name` against `file.name`. Status G (Blocked) gives $y = 1$. Statuses O, T, M, and B (Approved, Recommended, Pre-introduced, Conditionally usable) give $y = 0$. Statuses U, V, and Intended for phase-out are excluded from training and reported on their own. Files with no row in the list are not yet assigned a label.
- Why. U and V are "not recommended for new designs" (standardization and risk), and phase-out means existing use is being removed. None of them says the file is malicious, so charging $C_{MISS}$ for them would be wrong. The dropdown lists no blanks, so every row in the list has a status.
- Alternative. Strict mapping (every non-allowed status is $y = 1$), or approved-only (only O and T allowed). Both were set aside because they charge $C_{MISS}$ for policy statuses.
- Revisit. If the not-listed files turn out to be most of the alerts, the label covers too few alerts to score. If G-blocked files have few installs, `u_install_count` will predict the label almost by construction, and it can only be a feature if its snapshot date is before the cutoff.

## 2026-11-16: Split by time, cutoff 31 October

- Decision. The cutoff is 2026-10-31 00:00 local time, with daylight saving applied. Training holds alerts with a device time before the cutoff, and the held-out set holds alerts on or after it. Each `uuid` goes on the side of its earliest event across the three exports, so the 4 shared `uuid`s are counted once. The scored set is the matched openers only. Unmatched alerts have no y and are not scored.
- Why. The five blocked openers all fall before the cutoff, so the fit has them. Counts over 27,496 distinct `uuid`s: training has 1,072 allowed ($y = 0$), 5 blocked ($y = 1$), 4 conflicts, and 1 mixed exclusion. The held-out set has 139 allowed, 0 blocked, and 11 mixed exclusions. The held-out set therefore contains no blocked opener, so closing every alert costs 0 on the scored set, and no rule can show a miss caught.
- Alternative. The 2026-09-16 cutoff, which kept all five blocked openers in the held-out set and left the fit with no positives.
- Revisit. The five positives come from one 4-minute window on one night and may be one process on one device. Check that before any fit. A held-out score needs a blocked opener after the cutoff. If the cutoff is kept, the cost comparison can only report false-positive cost, and the score cannot say whether a missed attack is caught. A penalty is likely needed, because five positives are too few for unpenalized coefficients.

## 2026-11-16: Label is the process that opened the file

- Decision. The stand-in label is the status of `actor.app_name` on the 2026-11-16 product list, not the status of `file.name`. Blocked (G) is $y = 1$. Approved, Recommended, Pre-introduced, and Conditionally usable are $y = 0$. U, V, phase-out, and a name that is both blocked and allowed across versions stay out of the fit. An opener with no list row stays in the held-out set with no y. The list status and `u_install_count` stay out of the inputs, because the label is a function of that list and the list is dated after the cutoff.
- Why. `file.name` matched `prod_name` on 0 events. `actor.app_name` matches on 72 events in August–September (67 allowed, 4 conflicts, 1 mixed exclusion, 0 blocked), 171 in `Days_31_60.csv` (155 allowed, 11 mixed exclusions, 5 blocked), and 993 in `Days_01_30.csv` (993 allowed). The two later files share 4 matched `uuid`s. All 5 blocked events are on 2026-10-29, between 23:02 and 23:04 local time. An earlier note said 30 October; that date came from UTC.
- Alternative. Keep the label on the detected file. That join matches nothing, so the logistic regression has no rows.
- Revisit. The August–September fit has no $y = 1$, so log loss cannot learn a blocked opener from it. The five blocked events are inside the held-out month. Moving the cutoff to after 2026-10-30 would put them in training and leave a test set whose matched openers are all allowed, so closing every alert would cost 0 on that test. A blocked process that appears before the cutoff, with the same name in the test period, is what would make this label trainable.

## 2026-11-16: List date, and unlabeled alerts stay in the held-out set

- Decision. The product status list was downloaded on 2026-11-16 (10,000 rows). Its status and `u_install_count` are as of that day, so neither is a feature for alerts before the cutoff. Alerts whose detected `file.name` matches no `prod_name` stay in the held-out set for now, with no y.
- Why. On distinct `uuid`s, an exact match of `file.name` to `prod_name` hits 0 events in all three files. A containment match hits 9, 20, and 45. The unmatched events are 8,258 of 8,330, 11,885 of 12,056, and 8,117 of 9,110. The detected names are mostly `pdf`, `tmp`, `csv`, and `dll`, not product names. The only exact hits are `actor.app_name`: 72, 171, and 993 events, almost all status O, T, M, or B, and 5 events in `Days_31_60.csv` whose actor is status G. Among list rows, a positive install count is 1,163 of 6,889 allowed rows and 258 of 1,441 blocked rows, so the count does not separate the two labels, and the snapshot is after 2026-10-18.
- Alternative. Train on the actor-name matches and call the alert allowed when the process that opened the file is on the list. That labels the opener, not the file, and it leaves five blocked events to learn from.
- Revisit. If a join other than display name matches the detected file, those alerts leave the unlabeled held-out pile. The 10,000-row export is a round cap, so a complete list could also change the unmatched count. The expected-cost score stays undefined on the unlabeled rows until they have a y.

## 2026-11-17: Role-fit becomes an unsupervised process profile, and cannot be tested yet

- Decision. The role-fit input is replaced by an unsupervised profile. It groups users by their launch counts per process, with no job label. The profile uses only launches on 18–30 October 2026, before the cutoff, from `process_file_name.csv`. Users are matched by the short name, and processes with launches from at least 5 users are kept. The synthetic employee files are masks for names and devices only and do not supply any job label.
- Why. No real job titles are available, so a supervised role model cannot be trained on real users. A synthetic file that assigns titles at random would only show the pipeline runs.
- Result. 373 users in the profile, 901 processes kept, 5 clusters (sizes 42, 35, 81, 89, 126). Of 1,216 matched alerts, 962 have a profiled user, and all 962 fall in one cluster. The 5 blocked alerts have no profiled user, so the profile cannot be tested against a blocked opener.
- Alternative. Drop role-fit and fit on event features only. Get real job titles from HR or the directory, behind the mask, with security leadership's approval. Run the role pipeline on the synthetic file, labelled as a code check only. None of these was chosen.
- Revisit. If real job titles arrive, the supervised role model can be fit. If a blocked opener appears after the cutoff from a profiled user, rerun the test. The profile window is 13 days, not 30, because the process file starts on 18 October. A profile that puts all alert users in one cluster is not separating users, and the clustering should be checked before any result is reported.

## 2026-11-16: Pooled fit does not beat closing every alert

- Decision. Pool the three exports, one row per `uuid`, and fit logistic regression on the matched openers before 2026-10-31. Score the matched openers on or after that cutoff. Inputs are detection feature, disposition, severity, reason, file extension, hour, and the log of how many devices had already run that opener before the cutoff. The opener's name and the list status are not inputs. Compare with closing every alert.
- Why. The pool has 1,077 matched training alerts (1,072 allowed, 5 blocked) and 139 held-out matched alerts (139 allowed, 0 blocked). The five blocked alerts are one opener on one device, 1.9 minutes apart, and they have the same feature, disposition, severity, and reason as all 1,072 allowed training alerts: the same isolation feature, logged, informational, policy. Closing every held-out alert costs 0. An unpenalized fit has a largest coefficient of 64.9 and escalates 8 of the 139 at a cutoff of 0.5, all false positives, so its cost is $8 C_{FP}$. An L2 fit with $C = 1$ escalates none at that cutoff and ties closing every alert. At a cutoff of $0.1$ it escalates 52 false positives. Held-out log loss is $0.099$ unpenalized and $0.142$ with $C = 1$, against $0.0047$ for predicting the training rate $0.0046$ on every alert. `analysis.ipynb` reports this comparison. Its window simulation uses seed 20261116: in a window of 139 matched alerts the expected blocked count is 0.65, and 0.524 of draws have none. This run used the `python` on the machine, which is 3.15.2, not a 3.12 install. `.python-version` is 3.15.2.
- Alternative. A random split of the five blocked alerts, so some sit in the test. They are one incident, so a random split would score the model on the same opener and the same two minutes it trained on.
- Revisit. A blocked opener after 31 October, or the same blocked opener on an earlier day and a later day, would give the cost comparison a miss it could catch. Until then, closing every matched alert is the lower cost.
