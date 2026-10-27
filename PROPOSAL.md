# Proposal

## Who
Project Member/s
* Abel Rezene
* Given the sensitivity of the proposed data, I will be the only project member. 

## Hypothesis

An employee's endpoint activity predicts their job role, and an alert raised on activity that does not fit the predicted role is more likely a malicious actor than a false positive. The quantity is the probability that an endpoint security (antivirus) alert is malicious rather than a false positive, one probability per alert, given that user's activity over the 30 days before the alert.

## Data

1. Preferred, if approved: the organization I work for antivirus/EDR alert, logs joined to the Active Directory's (AD) job roles. The unit is one alert, with the user's prior 30 days of endpoint events (processes, file access, logons, USB use...etc). The label is the analyst's final verdict, false positive or malicious. These data cannot leave the organization and cannot be republished, and using employee data needs approval from security leadership.
2. Fallback: the CERT Insider Threat Test Dataset (Carnegie Mellon Software Engineering Institute). It is synthetic, about 1,000 simulated employees over about 17 months (release r4.2), with logon, device (USB), file, email and web logs, monthly directory files that give each user's role, and labelled insider-threat scenarios. It has no antivirus log, so its endpoint events stand in for one.

The gap: predicting role is a means, not the decision. Assigned roles in AD records lag reality (people change jobs), so the role label is noisy. CERT's behaviour is simulated, so its insiders may be easier to spot than real ones: bias that flatters the model. The split is by time: train on the earlier months, test on the later ones.

Terms: internal logs are never republished; `data/README.md` would describe the export, not the data. The CERT terms are to be confirmed; if they do not allow republishing, `data/README.md` gives the download command.

## Decision affected by the model

A SOC analyst decides for each antivirus alert whether to close it as a false positive or escalate it as a possible malicious actor (isolate the endpoint through the opened incident). The model adds a role-fit score: escalate when the predicted risk is high enough that an investigation costs less, on average, than closing a real attack. The costlier mistake is closing an alert on a real malicious actor as a false postive. Escalating a false positive costs analyst hours and an employee's lost working time. The model only ranks alerts for a human; it will not be used to judge employees, and that limit will be stated in the management communication and presentation.
