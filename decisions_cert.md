# Decisions, CERT r6.1

This file is the history of the CERT line only. The ICD 8031 history stays in `decisions.md`. Append an entry when a choice changes this line: the quantity, the data, the split, the model, the loss, or the action. Leave old entries in place.

## 2026-11-16: CERT r6.1, one USB connect

- Decision. The CERT stand-in for an 8031 alert is one `device.csv` Connect in release r6.1. $y = 1$ when that id is in the answer key. Train on connects before 2011-03-08, and hold out the rest, so scenarios 1 and 2 are in the fit and scenario 3 is the held-out attack. The scored model is logistic regression on the prior 30 days, after-hours, usual-PC mismatch, and the gap from the December role median. On the held-out connects it ties closing every connect, at equal costs and at a miss worth nine false escalations. Both cost $2 C_{MISS}$. `analysis_cert.ipynb` is this run.
- Why. The answer key marks 39 connects and 39 disconnects. Scoring both would count one insertion twice. The 39 connects are three campaigns: 3, then 34, then 2. A cutoff through the 34 would test the model on the campaign it just fit. The December median connect count is 0 for every role with more than two people, so the role gap correlates 0.999 with the log prior-connect count and does not change the cost. The louder held-out connect is rank 179, so catching it escalates 178 benign connects.
- Alternative. Scoring every `file.csv` row. The key marks 7 of those rows. Scoring `http.csv` would be required to see scenario 5, and that file is 78 GB. Using the job title as a coefficient was also set aside: that scores the role.
- Revisit. If `r6.1-4.csv` is in a later copy of the answers archive, scenario 4 gets a label. If a held-out connect clears the cost cutoff with fewer benign connects above it than $C_{MISS}/C_{FP}$, escalating can beat closing every connect.
