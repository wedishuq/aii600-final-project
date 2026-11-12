# Decisions

## 2026-11-11: Use Antivirus Detection Data

- **Decision.** Use antivirus detection events and historical endpoint activity to predict the probability that an alert is malicious using logistic regression.
- **Why.** Antivirus telemetry provides detection classifications and behavioral context for evaluating malicious activity. The model will use log loss and a cost-based escalation threshold.
- **Alternative.** Use broader endpoint security events or the CERT insider-threat dataset.
- **Revisit.** If reliable malicious/benign labels are unavailable or the antivirus data is insufficient for training and evaluation.
