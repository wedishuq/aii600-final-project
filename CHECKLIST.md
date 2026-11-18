# Checklist

Tick every line that the pushed `main` covers. A line you cannot tick needs one sentence saying why. This file is the list that counts. The ticks on the lab page do not.

## 1. Question

- [x] The question is one sentence, then one quantity with units and a time window.
- [x] The decision is named, and the loss or profit is a formula. The costlier mistake is named.
- [x] A layer diagram: data, model, prediction, decision.

## 2. Data

- [x] Source, unit of observation, sample size, time span, and how it was collected.
- [x] How the measurement differs from the quantity the decision needs, and whether that gap is bias or noise.
- [x] One plot of the raw data and one table of summary statistics, before any model.

## 3. Model

- [x] The model as equations. Each parameter in words, and the mechanism it stands for.
- [x] The assumptions, and the one you trust least.
- [ ] Simulated data from the model, checked against the real data. If the fit can recover known parameters, show that it does. The notebook draws a binomial window and a separated design; it does not recover a known finite coefficient from data drawn from the fitted model.

## 4. Uncertainty

- [ ] Every prediction carries a standard error, an interval, or a predictive distribution. Each held-out probability is a point estimate, with no standard error or interval.
- [ ] The error is measured out of sample, and you say how it grows as the forecast moves further from the data. Held-out log loss is one number for the whole window after 31 October, not a curve against how far past the cutoff an alert falls.
- [ ] Residuals plotted against time or against the prediction, and a statement of whether the error looks like noise or like bias. The held-out figure is a histogram of probabilities, and every held-out label is allowed, so residuals against time are not plotted.

## 5. Decision

- [x] An explicit rule from the prediction to the action, and why the loss picks that rule.
- [x] How the action changes when the main inputs change.
- [ ] What a better model or more data would be worth, in the units of the loss. The notebook prices the current rules, and it does not price what one more blocked opener, or an analyst verdict, would be worth in $C_{FP}$ and $C_{MISS}$.

## 6. Evaluation

- [x] A held-out set the model never saw, and a calibration check.
- [x] The method scored against a simple baseline in the units of the decision, not only RMSE or R².
- [x] Where the method wins, and where it ties.

## Decisions

- [x] `decisions.md` is the history: each choice, why, the alternative rejected, and what would change it. Old entries are still in the file.

## 7. Communicate

- [ ] `presentation.html` is a title slide plus the action, the reason, the risk with a number, and the value of being less wrong. It was rendered from `presentation.qmd` after the last edit to that file. The talk is due 9 December, and `presentation.qmd` is still the starter, so the HTML has not been rendered.
- [ ] The key effects are in plain language and in real units. Those sentences are in the notebook Decision section, not on a slide.
- [ ] The limits: where the model should not be trusted, what was assumed, and what you would do with more time or data. Those limits are in the notebook Limits section, not on a slide.

## Repository

- [x] Names and GitHub usernames are in `README.md`.
- [ ] A group reached `main` through pull requests, and each request names a `decisions.md` entry. One person; the course allows that person to commit straight to `main`.
- [x] `requirements.txt` pins the packages, and `.python-version` is the interpreter that ran the notebook. An R project uses `renv.lock` instead, which records the R version.
- [x] The `data` release holds the data files, or `data/README.md` gives the command that downloads them from the source. Each file has a SHA-256 there, and the notebook checks it. The notebook on `main` was run from the top and committed with its outputs. Secrets and fitted weights are not in git.
- [x] The split entry in `decisions.md` records the cutoff date, or the seed and the fraction.

## Disclosure

- [x] One line in `README.md`: which AI tools you used, and for what.
