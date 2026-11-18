"""CERT r6.1 device connects, scored like a Symantec file-detection alert.

The unit is one USB connect. y = 1 when that connect's id is in the r6.1
answer key. http.csv and email.csv are not read. Scenario 4 has no
observables file, so that user's connects inside the incident window are
not scored.
"""
import csv
import hashlib
import io
import tarfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

ROOT = Path(__file__).resolve().parent
R61 = ROOT / "data" / "12841247" / "r6.1"
ANSWERS = ROOT / "data" / "12841247" / "answers.tar.bz2"
EPOCH = datetime(2010, 1, 1)
# December activity only. The first device-labelled incident starts 6 January.
FREEZE = datetime(2011, 1, 1)
# Midnight after the last scenario-2 connect (7 March). The insiders.csv
# end for that scenario is 4 February, which is before those connects.
# Scenario 3's connects are 19 May, so this cutoff keeps each labelled
# scenario entirely on one side.
CUTOFF = datetime(2011, 3, 8)
WINDOW = 30 * 24 * 3600
SEED = 20261116
WORK_START = 8
WORK_END = 18

# Filled after the files were hashed. verify_hashes() checks these.
HASHES = {
    "device.csv": "4d95a992730325e0704869f2e03014132ee9f98e681d8bd9c47dbbbabb36d0ac",
    "logon.csv": "22b2671d1d8229c287837a958a3d2e26529ce3e2e6bbb8be06226d1e16064700",
    "file.csv": "25050ecf9f40d9cf599dd594b43a79790e4bce29095f5bd3cfb189a0f74bd2c7",
    "answers.tar.bz2": "ed21bf921def01e97326b314f2d1fa77651a945bd31bf513095f8ac7658c9ddd",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_hashes():
    found = {}
    for name in ("device.csv", "logon.csv", "file.csv"):
        found[name] = sha256(R61 / name)
        expected = HASHES.get(name)
        if expected and found[name] != expected:
            raise SystemExit(f"{name} hash {found[name]} does not match")
    found["answers.tar.bz2"] = sha256(ANSWERS)
    if found["answers.tar.bz2"] != HASHES["answers.tar.bz2"]:
        raise SystemExit("answers.tar.bz2 hash does not match CHECKSUMS-sha256.txt")
    return found


def stamp_of(text):
    """Parse MM/DD/YYYY HH:MM:SS into seconds since 2010-01-01 and a datetime."""
    month, day, year = text[:10].split("/")
    hour, minute, second = text[11:19].split(":")
    when = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    return int((when - EPOCH).total_seconds()), when


def after_hours(when):
    return when.weekday() >= 5 or when.hour < WORK_START or when.hour >= WORK_END


def month_index(when):
    return when.year * 12 + when.month


def load_answers():
    """Device-event ids from the r6.1 answer key, plus incident windows."""
    malicious = {}
    incidents = []
    with tarfile.open(ANSWERS, "r:bz2") as archive:
        names = set(archive.getnames())
        text = archive.extractfile("answers/insiders.csv").read().decode("utf-8", "replace")
        for row in csv.DictReader(io.StringIO(text)):
            if row["dataset"] != "6.1":
                continue
            start, start_dt = stamp_of(row["start"])
            end, end_dt = stamp_of(row["end"])
            member = "answers/" + row["details"]
            incident = {
                "scenario": int(row["scenario"]),
                "user": row["user"],
                "start": start_dt,
                "end": end_dt,
                "start_sec": start,
                "end_sec": end,
                "details": row["details"],
                "has_file": member in names,
                "device_ids": 0,
            }
            if member in names:
                raw = archive.extractfile(member).read().decode("utf-8", "replace")
                for fields in csv.reader(io.StringIO(raw)):
                    if fields and fields[0] == "device":
                        malicious[fields[1]] = incident["scenario"]
                        incident["device_ids"] += 1
            incidents.append(incident)
    return malicious, incidents


def load_roles():
    """user -> {month_index: role}. Later months are not used to fill earlier ones."""
    roles = defaultdict(dict)
    for path in sorted((R61 / "LDAP").glob("*.csv")):
        year, month = path.stem.split("-")
        idx = int(year) * 12 + int(month)
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                roles[row["user_id"]][idx] = row["role"]
    return roles


def role_at(roles, user, idx):
    months = roles.get(user)
    if not months:
        return None
    if idx in months:
        return months[idx]
    earlier = [key for key in months if key < idx]
    if not earlier:
        return None
    return months[max(earlier)]


def window_count(times, moment):
    if times.size == 0:
        return 0
    hi = np.searchsorted(times, moment, side="left")
    lo = np.searchsorted(times, moment - WINDOW, side="left")
    return int(hi - lo)


def build_frame(malicious, incidents):
    """Stream the three endpoint logs and return one row per USB connect."""
    csv.field_size_limit(10**7)
    unscored = [
        item for item in incidents if not item["has_file"]
    ]
    connect_times = defaultdict(list)
    after_logons = defaultdict(list)
    files_out = defaultdict(list)
    pc_counts = defaultdict(Counter)
    rows = []
    disconnect_ids = set()
    freeze_sec = int((FREEZE - EPOCH).total_seconds())
    n_file_out = 0

    with (R61 / "logon.csv").open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["activity"] != "Logon":
                continue
            sec, when = stamp_of(row["date"])
            if sec < freeze_sec:
                pc_counts[row["user"]][row["pc"]] += 1
            if after_hours(when):
                after_logons[row["user"]].append(sec)

    with (R61 / "file.csv").open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["to_removable_media"] != "True":
                continue
            sec, _when = stamp_of(row["date"])
            files_out[row["user"]].append(sec)
            n_file_out += 1

    with (R61 / "device.csv").open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["activity"] == "Disconnect":
                disconnect_ids.add(row["id"])
                continue
            if row["activity"] != "Connect":
                continue
            sec, when = stamp_of(row["date"])
            user = row["user"]
            connect_times[user].append(sec)
            scenario = malicious.get(row["id"], 0)
            scored = True
            for item in unscored:
                if user == item["user"] and item["start_sec"] <= sec <= item["end_sec"]:
                    scored = False
                    break
            rows.append((
                sec, user, row["pc"], 1 if scenario else 0, scenario,
                int(after_hours(when)), month_index(when), scored, when,
            ))

    usual = {
        user: sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for user, counts in pc_counts.items()
        if counts
    }
    arrays = {}
    for store in (connect_times, after_logons, files_out):
        for user, values in store.items():
            store[user] = np.asarray(values, dtype=np.int64)
            store[user].sort()

    n = len(rows)
    prior_c = np.zeros(n, dtype=np.int32)
    prior_a = np.zeros(n, dtype=np.int32)
    prior_f = np.zeros(n, dtype=np.int32)
    mismatch = np.zeros(n, dtype=np.int8)
    by_user = defaultdict(list)
    for i, row in enumerate(rows):
        by_user[row[1]].append(i)
    empty = np.asarray([], dtype=np.int64)
    for user, idxs in by_user.items():
        ctimes = connect_times.get(user, empty)
        atimes = after_logons.get(user, empty)
        ftimes = files_out.get(user, empty)
        usual_pc = usual.get(user)
        for i in idxs:
            moment = rows[i][0]
            prior_c[i] = window_count(ctimes, moment)
            prior_a[i] = window_count(atimes, moment)
            prior_f[i] = window_count(ftimes, moment)
            pc = rows[i][2]
            mismatch[i] = int(usual_pc is not None and pc != usual_pc)

    key_ids = set(malicious)
    matched = sum(1 for row in rows if row[4])
    disconnect_hits = len(key_ids & disconnect_ids)
    frame = pd.DataFrame({
        "sec": [row[0] for row in rows],
        "y": [row[3] for row in rows],
        "scenario": [row[4] for row in rows],
        "after_hours": [row[5] for row in rows],
        "month_index": [row[6] for row in rows],
        "scored": [row[7] for row in rows],
        "when": [row[8] for row in rows],
        "prior_connects": prior_c,
        "prior_after_logons": prior_a,
        "prior_files_out": prior_f,
        "pc_mismatch": mismatch,
        "user": [row[1] for row in rows],
    })
    meta = {
        "connects": n,
        "disconnects": len(disconnect_ids),
        "file_to_removable": n_file_out,
        "answer_device_ids": len(key_ids),
        "answer_ids_that_are_connects": matched,
        "answer_ids_that_are_disconnects": disconnect_hits,
        "answer_ids_absent": len(key_ids) - matched - disconnect_hits,
    }
    return frame, usual, meta


def add_role_gap(frame, roles):
    """Excess log connect rate over the role's December 2010 median.

    The median uses connects in the 30 days before FREEZE, and the December
    LDAP role. It does not use activity from the incident months.
    """
    dec = month_index(FREEZE - timedelta(days=1))
    freeze_sec = int((FREEZE - EPOCH).total_seconds())
    in_december = (frame["sec"] >= freeze_sec - WINDOW) & (frame["sec"] < freeze_sec)
    per_user = frame.loc[in_december].groupby("user").size()
    records = []
    for user, months in roles.items():
        role = months.get(dec)
        if role is None:
            continue
        records.append((role, int(per_user.get(user, 0))))
    baseline = pd.DataFrame(records, columns=["role", "connects"])
    medians = baseline.groupby("role")["connects"].median()
    sizes = baseline.groupby("role")["connects"].size()
    global_median = float(baseline["connects"].median())
    role_name = [
        role_at(roles, user, idx)
        for user, idx in zip(frame["user"], frame["month_index"])
    ]
    frame = frame.copy()
    frame["role"] = role_name
    chosen = frame["role"].map(medians).fillna(global_median).astype(float)
    frame["role_median"] = chosen
    frame["role_gap"] = np.log1p(frame["prior_connects"]) - np.log1p(chosen)
    table = pd.DataFrame({"users": sizes, "median_connects": medians}).sort_values("users", ascending=False)
    return frame, table, global_median


def design(frame, with_role):
    columns = [
        frame["after_hours"].to_numpy(dtype=float),
        np.log1p(frame["prior_connects"].to_numpy(dtype=float)),
        np.log1p(frame["prior_after_logons"].to_numpy(dtype=float)),
        np.log1p(frame["prior_files_out"].to_numpy(dtype=float)),
        frame["pc_mismatch"].to_numpy(dtype=float),
    ]
    names = [
        "after_hours",
        "log_prior_connects",
        "log_prior_after_logons",
        "log_prior_files_out",
        "pc_mismatch",
    ]
    if with_role:
        columns.append(frame["role_gap"].to_numpy(dtype=float))
        names.append("role_gap")
    return np.column_stack(columns), names


def heldout_cost(p, y, ratio):
    """ratio = C_MISS / C_FP. Escalate when p > 1 / (1 + ratio)."""
    cutoff = 1 / (1 + ratio)
    escalate = p > cutoff
    false_pos = int((escalate & (y == 0)).sum())
    misses = int((~escalate & (y == 1)).sum())
    return cutoff, false_pos, misses


def wald_se(model, x):
    """Independent-connect Wald SE. Too small if one campaign is many rows."""
    p = np.clip(model.predict_proba(x)[:, 1], 1e-8, 1 - 1e-8)
    weight = p * (1 - p)
    design_x = np.column_stack([np.ones(len(x)), x])
    hess = (design_x * weight[:, None]).T @ design_x
    cov = np.linalg.pinv(hess)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    return se, cov


def probability_interval(model, x):
    """Delta-method interval for p. Same independence assumption as wald_se."""
    _se, cov = wald_se(model, x)
    design_x = np.column_stack([np.ones(len(x)), x])
    se_eta = np.sqrt(np.clip(np.sum((design_x @ cov) * design_x, axis=1), 0, None))
    eta = model.intercept_[0] + x @ model.coef_[0]
    p = 1 / (1 + np.exp(-eta))
    se_p = p * (1 - p) * se_eta
    low = np.clip(p - 1.96 * se_p, 0, 1)
    high = np.clip(p + 1.96 * se_p, 0, 1)
    return p, low, high


def fit_one(train, test, with_role, kwargs):
    y_train = train["y"].to_numpy(dtype=int)
    y_test = test["y"].to_numpy(dtype=int)
    x_train, names = design(train, with_role)
    x_test, _ = design(test, with_role)
    model = LogisticRegression(solver="lbfgs", max_iter=800, **kwargs)
    model.fit(x_train, y_train)
    p_train = model.predict_proba(x_train)[:, 1]
    p_test = model.predict_proba(x_test)[:, 1]
    return {
        "model": model,
        "names": names,
        "x_train": x_train,
        "x_test": x_test,
        "p_train": p_train,
        "p_test": p_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_log_loss": float(log_loss(y_train, np.clip(p_train, 1e-6, 1 - 1e-6), labels=[0, 1])),
        "test_log_loss": float(log_loss(y_test, np.clip(p_test, 1e-6, 1 - 1e-6), labels=[0, 1])),
        "max_abs_coef": float(np.max(np.abs(model.coef_))),
    }


def incident_table(frame, incidents):
    rows = []
    for item in incidents:
        part = frame[frame["scenario"] == item["scenario"]]
        by_user = frame[frame["user"] == item["user"]]
        in_window = by_user[
            (by_user["sec"] >= item["start_sec"]) & (by_user["sec"] <= item["end_sec"])
        ]
        if len(part):
            role = part["role"].iloc[0]
        elif len(by_user):
            role = by_user["role"].iloc[0]
        else:
            role = None
        rows.append({
            "scenario": item["scenario"],
            "user": item["user"],
            "has_answer_file": item["has_file"],
            "device_ids_in_key": item["device_ids"],
            "connects_labelled": int(len(part)),
            "connects_in_summary_window": int(len(in_window)),
            "connects_by_user": int(len(by_user)),
            "start": item["start"].isoformat(sep=" "),
            "end": item["end"].isoformat(sep=" "),
            "role": role,
            "after_hours_labelled": None if part.empty else int(part["after_hours"].sum()),
            "pc_mismatch_labelled": None if part.empty else int(part["pc_mismatch"].sum()),
        })
    return pd.DataFrame(rows)


def save_plots(frame, test, p_test, base_rate):
    fig_dir = ROOT / "fig"
    fig_dir.mkdir(exist_ok=True)
    week = frame["sec"] // (7 * 24 * 3600)
    counts = frame.groupby(week).size()
    malicious = frame[frame["y"] == 1].groupby(week).size()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(counts.index, counts.values, color="0.75", width=1.0, label="all connects")
    ax2 = ax.twinx()
    ax2.plot(malicious.index, malicious.values, color="C3", marker="o", label="answer-key connects")
    ax.set_xlabel("week since 2010-01-01")
    ax.set_ylabel("USB connects")
    ax2.set_ylabel("answer-key connects")
    ax.set_title("Device connects by week, before the model")
    fig.tight_layout()
    fig.savefig(fig_dir / "cert_weekly.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.hist(p_test, bins=40, color="0.35")
    ax.axvline(base_rate, color="C0", ls="--", label=f"training rate {base_rate:.6f}")
    ax.set_xlim(0, max(0.012, float(np.max(p_test)) * 1.05))
    ax.set_xlabel("held-out P(connect is in the answer key)")
    ax.set_ylabel("USB connects")
    ax.set_title("Equal-cost cutoff is 0.5, off this scale to the right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "cert_heldout_p.png", dpi=120)
    plt.close(fig)

    order = np.argsort(test["sec"].to_numpy())
    sec = test["sec"].to_numpy()[order]
    resid = (test["y"].to_numpy() - p_test)[order]
    week_t = sec // (7 * 24 * 3600)
    tmp = pd.DataFrame({"week": week_t, "resid": resid})
    by_week = tmp.groupby("week")["resid"].mean()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.axhline(0, color="0.5", lw=1)
    ax.plot(by_week.index, by_week.values, color="0.2")
    ax.set_xlabel("week since 2010-01-01")
    ax.set_ylabel("mean residual, y − p")
    ax.set_title("Held-out residuals by week")
    fig.tight_layout()
    fig.savefig(fig_dir / "cert_residual_week.png", dpi=120)
    plt.close(fig)


def layers_plot():
    fig_dir = ROOT / "fig"
    fig_dir.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")
    boxes = [
        (0.3, "USB connects"),
        (2.7, "30-day history\nand LDAP role"),
        (5.1, "logistic p"),
        (7.5, "close or escalate\nby the cost cutoff"),
    ]
    for x, label in boxes:
        ax.add_patch(plt.Rectangle((x, 0.5), 2.0, 1.0, fill=False))
        ax.text(x + 1.0, 1.0, label, ha="center", va="center")
    for x in (2.3, 4.7, 7.1):
        ax.annotate("", xy=(x + 0.35, 1.0), xytext=(x, 1.0), arrowprops=dict(arrowstyle="->"))
    fig.tight_layout()
    fig.savefig(fig_dir / "cert_layers.png", dpi=120)
    plt.close(fig)


def prepare(check_hash=True):
    """Load, label, and split. Does not fit."""
    hashes = verify_hashes() if check_hash else {}
    malicious, incidents = load_answers()
    roles = load_roles()
    frame, _usual, meta = build_frame(malicious, incidents)
    frame, role_table, global_median = add_role_gap(frame, roles)
    cutoff_sec = int((CUTOFF - EPOCH).total_seconds())
    scored = frame[frame["scored"]].copy()
    train = scored[scored["sec"] < cutoff_sec]
    test = scored[scored["sec"] >= cutoff_sec]
    y_train = train["y"].to_numpy(dtype=int)
    if y_train.sum() == 0 or y_train.sum() == len(y_train):
        raise SystemExit("training slice has one class; the cutoff does not match the incidents")
    positives = scored[scored["y"] == 1]
    early = positives[positives["scenario"].isin([1, 2])]
    late = positives[positives["scenario"] == 3]
    if len(early) == 0 or early["sec"].max() >= cutoff_sec or (len(late) and late["sec"].min() < cutoff_sec):
        raise SystemExit("cutoff splits a device-labelled scenario; refusing to fit")
    return {
        "hashes": hashes,
        "meta": meta,
        "incidents": incident_table(frame, incidents),
        "role_table": role_table,
        "global_median": global_median,
        "frame": frame,
        "train": train,
        "test": test,
        "base_rate": float(y_train.mean()),
        "excluded": int((~frame["scored"]).sum()),
    }


def fit_all(prepared):
    train, test = prepared["train"], prepared["test"]
    fits = {
        "history": fit_one(train, test, False, {"C": np.inf}),
        "history_role": fit_one(train, test, True, {"C": np.inf}),
        "history_role_l2": fit_one(train, test, True, {"C": 1.0, "l1_ratio": 0}),
    }
    out = dict(prepared)
    out["fits"] = fits
    return out


def analyze(check_hash=True):
    return fit_all(prepare(check_hash=check_hash))


def report(result):
    meta = result["meta"]
    train, test = result["train"], result["test"]
    print("hashes", result["hashes"])
    print("meta", meta)
    print("excluded connects", result["excluded"])
    print(result["incidents"].to_string(index=False))
    print("role medians, December 2010, 30 days before 1 January")
    print(result["role_table"].to_string())
    print("global median", result["global_median"])
    print(
        "train", len(train), "positives", int(train["y"].sum()),
        "test", len(test), "positives", int(test["y"].sum()),
        "rate", f"{result['base_rate']:.6f}",
    )
    feature_cols = [
        "after_hours", "prior_connects", "prior_after_logons",
        "prior_files_out", "pc_mismatch", "role_gap",
    ]
    print("training means by label")
    print(train.groupby("y")[feature_cols].mean().to_string())
    print("training medians by label")
    print(train.groupby("y")[feature_cols].median().to_string())
    gap = train["role_gap"].to_numpy(dtype=float)
    raw = np.log1p(train["prior_connects"].to_numpy(dtype=float))
    print("corr(role_gap, log_prior_connects)", round(float(np.corrcoef(gap, raw)[0, 1]), 4))
    for name, fit in result["fits"].items():
        print(
            name,
            "max |coef|", round(fit["max_abs_coef"], 3),
            "train log loss", round(fit["train_log_loss"], 6),
            "test log loss", round(fit["test_log_loss"], 6),
            "test p max", round(float(fit["p_test"].max()), 6),
        )
        coef = fit["model"].coef_[0]
        print("  intercept", round(float(fit["model"].intercept_[0]), 3))
        for feature, value in zip(fit["names"], coef):
            print(f"  {feature} {value:.4f}")
        y_test = fit["y_test"]
        for ratio in (1, 9):
            cutoff, false_pos, misses = heldout_cost(fit["p_test"], y_test, ratio)
            print(
                f"  ratio {ratio} cutoff {cutoff:.4f} false_pos {false_pos} misses {misses} "
                f"cost {false_pos} C_FP + {misses} C_MISS"
            )
    y_test = test["y"].to_numpy(dtype=int)
    chosen = result["fits"]["history_role"]
    print(f"close every connect: 0 C_FP + {int(y_test.sum())} C_MISS on {len(test)} held-out connects")
    p_chosen = chosen["p_test"]
    print(
        "held-out mean p", round(float(p_chosen.mean()), 6),
        "observed rate", round(float(y_test.mean()), 6),
    )
    # How many benign connects outrank each held-out attack.
    order = np.argsort(-p_chosen)
    y_order = y_test[order]
    p_order = p_chosen[order]
    hits = np.flatnonzero(y_order == 1)
    for rank in hits:
        ahead = int(rank)  # benign rows strictly above this attack
        print(
            "attack rank", int(rank) + 1,
            "p", round(float(p_order[rank]), 6),
            "connects with a higher p", ahead,
        )
    constant = np.full(len(y_test), result["base_rate"])
    print(
        "constant-rate held-out log loss",
        round(float(log_loss(y_test, constant, labels=[0, 1])), 6),
    )
    se, _cov = wald_se(chosen["model"], chosen["x_train"])
    print("wald se, unpenalized with role, treating connects as independent")
    print("  intercept", round(float(se[0]), 4))
    for feature, value in zip(chosen["names"], se[1:]):
        print(f"  {feature} {value:.4f}")
    pos = test["y"].to_numpy() == 1
    if pos.any():
        p, low, high = probability_interval(chosen["model"], chosen["x_test"][pos])
        print("held-out positive connects, p and 95% interval")
        for i, (pi, lo, hi) in enumerate(zip(p, low, high)):
            print(f"  {i} p {pi:.4f} [{lo:.4f}, {hi:.4f}]")
    rng = np.random.default_rng(SEED)
    draws = rng.binomial(len(test), result["base_rate"], size=10000)
    print(f"expected answer-key connects in a window of {len(test)}: {draws.mean():.2f}")
    print(f"share of draws with none: {(draws == 0).mean():.3f}")
    layers_plot()
    save_plots(result["frame"], test, chosen["p_test"], result["base_rate"])
    print("plots written")


if __name__ == "__main__":
    report(analyze())
